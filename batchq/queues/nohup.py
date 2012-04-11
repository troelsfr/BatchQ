from batchq.core import batch
from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.utils import FileCommander
from batchq.shortcuts.shell import home_create_dir, send_command
from datetime import timedelta
import re

str_time_regex = re.compile(r'((?P<days>\d+?)days?, *)?((?P<hours>\d+?)hr *)?((?P<minutes>\d+?)m *)?((?P<seconds>\d+?)s *)?')
def str_to_timedelta(s):
    m = str_time_regex.search(s)
    if not m: return timedelta(0)
    kwargs = dict([(a,int(b)) for a,b in m.groupdict().iteritems() if b])
    return timedelta(**kwargs)

def format_time(t):
    if isinstance(t, str):
        t = str_to_timedelta(t).total_seconds()        
    elif isinstance(t, timedelta):
        t = t.total_seconds()
        

    if t < 0: return -1
    if t/60 - t/60. == 0.:
        return int(t/60)
    return int(t/60+1)

class NoHUP(batch.BatchQ):

    _r = batch.WildCard(reverse = True)
    _ = batch.WildCard()
    _2 = batch.WildCard()
    _last = batch.WildCard( select = 0, reverse = True)

    command = batch.Property("echo Hello World > execution.txt",display="Command to execute: ")
    working_directory = batch.Property(display="Specify a working directory: ")
    input_directory = batch.Property(".", display="Specify an input directory: ")
    output_directory = batch.Property(".", display="Specify an output directory: ")

    # TODO: 
#    input_paths = batch.Property([], display="Specify an input paths: ")



    subdirectory = batch.Property(".", verbose = False)
    prior = batch.Property("", verbose = False)    
    post = batch.Property("", verbose = False)    

    server = batch.Property("localhost", display="Server: ", verbose=False)
    processes = batch.Property(1, display="Number of processes: ", verbose = False) 
    time = batch.Property(-1, display="Wall time: ", verbose = False, formatter = format_time)    
    mpi = batch.Property(False, display="Use MPI: ", verbose = False)    
    threads = batch.Property(1, display="OpenMP threads: ", verbose = False)    
    memory = batch.Property(-1, display="Max. memory: ", verbose = False)    
    diskspace = batch.Property(-1, display="Max. space: ", verbose = False)    

    overwrite_nodename_with = batch.Property("", verbose = False)
    overwrite_submission_id = batch.Property("", verbose = False)

    terminal = batch.Controller(BashTerminal)


    #### STUFF FOR SYSTEM IDENTIFICATION
    whoami = batch.Function() \
        .whoami()

    overwrite_nodename = batch.Function(verbose=True)\
        .overwrite_nodename(overwrite_nodename_with)

    nodename = batch.Function(verbose=True)\
        .nodename()

    nodeid = batch.Function(verbose=True) \
        .nodename().Qslugify(_)

    system_info = batch.Function(verbose=True) \
        .system_info()

    system_string = batch.Function(verbose=True) \
        .system_string()

    ## TESTED AND WORKING
    hash_input = batch.Function(verbose=True,cache = 5) \
        .entrance().chdir(_).directory_hash(input_directory,True,True) \
        .Qslugify(command).Qjoin(_,"-",_)

    ## TESTED AND WORKING
    identifier = batch.Function(cache = 5) \
        .Qslugify(command).Qstr(overwrite_submission_id).Qjoin(_,"-",_).Qstore("id") \
        .Qstr(overwrite_submission_id).Qequal("",_).Qdo(2).Qcall(hash_input).Qstore("id") \
        .Qget("id")

    identifier_filename = batch.Function(identifier,cache = 5).Qjoin(".batchq_",_)

    ## TESTED AND WORKING
    get_subdirectory = batch.Function(verbose=True, cache = 5) \
        .Qstr(subdirectory).Qstore("subdir") \
        .Qequal(_,".").Qdo(3).Qcall(identifier_filename).Qget("id").Qstore("subdir") \
        .Qget("subdir")


    ## TESTED AND WORKING
    _create_workdir = batch.Function(verbose=True,cache=5) \
        .entrance().chdir(_) \
        .isdir(working_directory).Qdon(1).mkdir(working_directory, True) \
        .chdir(working_directory) \
        .Qcall(get_subdirectory) \
        .isdir(_).Qdon(2).Qget("subdir").mkdir(_, True) \
        .Qget("subdir").chdir(_).pwd().Qstore("workdir")

    create_workdir = batch.Function(verbose=True) \
        .Qcall(_create_workdir).Qget("workdir").chdir(_) \
        .Qget("workdir")

    ### TESTED AND WORKING
    prepare_incopy = batch.Function(create_workdir, verbose=True) \
        .Qset("sync_cache",False) \
        .entrance().Qpjoin(_,input_directory).Qstore("indir") \
        .Qpjoin(_,"*").Qget("workdir")

    ### TESTED AND WORKING
    prepare_outcopy = batch.Function(create_workdir, verbose=True) \
        .Qset("sync_cache",False) \
        .entrance().Qpjoin(_,output_directory).Qstore("outdir") \
        .Qget("workdir").Qpjoin(_,"*").Qget("outdir")
    
    ### TESTED AND WORKING
    send = batch.Function(prepare_incopy , verbose=True, enduser=True) \
        .cp(_r, _r, True).Qdon(1).Qthrow("Failed to transfer files.")

    ### TESTED AND WORKING
    recv = batch.Function(prepare_outcopy, verbose=True, enduser=True) \
        .cp(_r, _r).Qdon(1).Qthrow("Failed to transfer files.")

    ### TESTED AND WORKING
    pid = batch.Function(create_workdir,verbose=True, enduser=True, cache=5) \
        .Qjoin(identifier_filename,".pid").Qstore("pid_file") \
        .isfile(_).Qdon(2).Qstr("-1").Qreturn() \
        .Qget("pid_file").cat(_)



    ### TESTED AND WORKING
    pending = batch.Function(verbose=True, enduser=True, cache=5) \
        .Qbool(False)

    ## TESTED AND WORKING
    submitted = batch.Function(create_workdir,verbose=True, enduser=True, cache=5) \
        .Qcall(identifier_filename).Qjoin(_,".pid").isfile(_)

    lazy_finished = batch.Function(create_workdir,verbose=True, enduser=True, cache=5) \
        .Qjoin(identifier_filename,".finished").isfile(_).Qdo(2).Qbool(True).Qreturn() \
        .Qbool(False)

    finished = batch.Function(lazy_finished,verbose=True, enduser=True, cache=5)

    lazy_running = batch.Function(lazy_finished,verbose=True, enduser=True, cache=5) \
        .Qdo(2).Qbool(False).Qreturn() \
        .Qjoin(identifier_filename,".running").isfile(_).Qdo(2).Qbool(True).Qreturn() \
        .Qbool(False)
       
    running = batch.Function(lazy_running,verbose=True, enduser=True, cache=5) \
        .Qdon(2).Qbool(False).Qreturn() \
        .Qcall(pid).Qstore("pid").Qequal(_,"-1").Qdo(2).Qbool(False).Qreturn() \
        .Qget("pid").isrunning(_)

    failed = batch.Function(lazy_finished, enduser=True, cache=5) \
        .Qdon(2).Qbool(False).Qreturn() \
        .Qjoin(identifier_filename,".finished").cat(_).Qint(_).Qequal(_,0).Qnot(_)
        


    ## TODO: TEST
    prepare_submission = batch.Function() \
         .Qstr(threads).Qjoin("export  OMP_NUM_THREADS=",_).send_command(_) \
         .Qset("command_prepend","").Qbool(mpi).Qdo(3).Qstr(processes).Qjoin("mpirun -np ", _, " ").Qstore("command_prepend")

    ## TESTED AND WORKING
    startjob = batch.Function(create_workdir,verbose=True) \
        .Qclear_cache() \
        .Qcall(prepare_submission) \
        .send_command(prior) \
        .Qget("command_prepend") \
        .Qcall(identifier_filename, 1) \
        .Qjoin("(touch ",_last, ".submitted ;  touch ",_last,".running ; ", command, " 1> ",_last,".running 2> ",_last,".error  && echo $! > ",_last,".pid  ;  echo $? > ",_last,".finished )") \
        .send_command(_)


    ## TESTED AND WORKING
    submit = batch.Function(send, verbose=True, enduser=True) \
        .Qcall(startjob)


    ## TESTED AND WORKING
    stdout = batch.Function(submitted,verbose=True, enduser=True) \
        .Qdo(2).Qcall(identifier_filename).cat(_)

    # TODO:
    stderr = batch.Function(submitted,verbose=True, enduser=True) \
        .Qprint("not implemented yet")

    log = batch.Function(submitted,verbose=True, enduser=True) \
        .Qprint("No log implemented for SSH. Use stderr and stdout")


    ## TESTED AND WORKING
    clean = batch.Function(create_workdir,verbose=True, enduser=True) \
        .Qdo(1).rm(".batchq*", force = True)

    ## TESTED AND WORKING
    delete = batch.Function(create_workdir,verbose=True, enduser=True) \
        .Qdo(2).Qget("workdir").rm(_, force = True, recursively = True)

    ## TODO: TEST
    cancel = batch.Function(pid, verbose=True, enduser=True).kill(_)

    ### TESTED AND WORKING
    status = batch.Function(verbose=True, enduser=True) \
        .Qcall(submitted).Qdon(2).Qstr("was not submitted").Qreturn() \
        .Qcall(running).Qdo(2).Qstr("running").Qreturn() \
        .Qcall(finished).Qdo(2).Qstr("finished").Qreturn() \
        .Qcall(pending).Qdo(2).Qstr("pending").Qreturn() \
        .Qcall(failed).Qdo(2).Qstr("failed").Qreturn() \
        .Qcall(submitted).Qdo(2).Qstr("pre-pending").Qreturn() \
        .Qstr("unknown status")


    job = batch.Function(verbose=True, enduser=True) \
        .Qcall(submitted).Qdon(6).Qprint("Uploading input directory:",input_directory,"->",create_workdir).Qcall(send).Qprint("Submitting job on ",server).Qcall(startjob).Qstr("").Qreturn() \
        .Qcall(pending).Qdo(3).Qprint("Job is pending.").Qstr("").Qreturn() \
        .Qcall(running).Qdo(3).Qprint("Job is running.").Qstr("").Qreturn() \
        .Qcall(failed).Qdo(3).Qprint("Job has failed:\n\n").Qcall(log).Qreturn() \
        .Qcall(finished).Qdo(8).Qprint("Job has finished.").Qcall(recv).Qdo(1).Qprint("Using cache.").Qdon(1).Qprint("Files retrieved.").Qstr("").Qreturn() \
        .Qcall(submitted).Qdo(3).Qprint("Job is pre-pending (i.e. submitted but not in the batch system).").Qstr("").Qreturn() \
        .Qprint("Your job has an unknown status.").Qstr("")


class NoHUPSSH(NoHUP):
    _ = batch.WildCard()
    _r = batch.WildCard(reverse=True)

    username = batch.Property(display="Username: ")
    password = batch.Property(password = True, display="Password: ")
    server = batch.Property("localhost", display="Server: ")
    port = batch.Property(22, display="Port: ")



    filecommander = batch.Controller(FileCommander,server,username, password, port)
    local_terminal = batch.Controller(BashTerminal,q_instance = filecommander.local)
    terminal = batch.Controller(BashTerminal,q_instance = filecommander.remote)


    reconnect = batch.Function() \
        .connection_lost().Qdo(1).connect(server,username, password, port) \
        .Qcontroller("filecommander") \
        .connection_lost().Qdo(1).connect(server,username, password, port) 

#    hash_input_directory = batch.Function(verbose=True) \
#        .Qcontroller("local_terminal") \
#        .entrance().chdir(_).directory_hash(NoHUP.input_directory,True,True)

    ## TESTED AND WORKING
    hash_input = batch.Function(verbose=True).Qcontroller("local_terminal") \
        .entrance().chdir(_).directory_hash(NoHUP.input_directory,True,True) \
        .Qdo(2).Qslugify(NoHUP.command).Qjoin(_,"-",_)

    ## TESTED AND WORKING
#    hash_output = batch.Function(verbose=True).Qcontroller("local_terminal") \
#        .entrance().chdir(_).directory_hash(NoHUP.output_directory,True,True) \
#        .Qdo(2).Qslugify(NoHUP.command).Qjoin(_,"-",_,"-",_,"-",_)

    ## TESTED AND WORKING
    prepare_incopy = batch.Function(NoHUP.create_workdir) \
        .Qset("sync_cache",False) \
        .Qcontroller("local_terminal") \
        .pwd().Qpjoin(_,NoHUP.input_directory).Qstore("indir")  \
        .Qget("workdir")

    ## TESTED AND WORKING
    prepare_outcopy = batch.Function(NoHUP.create_workdir).Qcontroller("local_terminal") \
        .Qset("sync_cache",False)  \
        .push_entrance().isdir(NoHUP.output_directory).Qdon(1).mkdir(NoHUP.output_directory, True).popd() \
        .entrance().Qpjoin(_,NoHUP.output_directory).Qstore("outdir") \
        .entrance().Qpjoin(_,NoHUP.input_directory).Qstore("indir")  \
        .Qget("outdir").Qget("workdir").Qget("indir")

    ## TESTED AND WORKING
    send = batch.Function(prepare_incopy , verbose=True) \
        .Qcontroller("filecommander").sync(_r,_r, mode = FileCommander.MODE_LOCAL_REMOTE) \
        .Qequal(_, False).Qdo(1).Qset("sync_cache",True) \
        .Qget("sync_cache")
    
    ## TESTED AND WORKING
    recv = batch.Function(prepare_outcopy , verbose=True) \
        .Qcontroller("filecommander").sync(_r,_r, mode = FileCommander.MODE_REMOTE_LOCAL, diff_local_dir =_r) \
        .Qequal(_, False).Qdo(1).Qset("sync_cache",True) \
        .Qget("sync_cache")

    
