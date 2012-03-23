from batchq.core import batch
from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.utils import FileCommander
from batchq.shortcuts.shell import home_create_dir, send_command

class NoHUP(batch.BatchQ):
    _r = batch.WildCard(reverse = True)
    _ = batch.WildCard()

    command = batch.Property(display="Command to execute: ")
    working_directory = batch.Property(display="Specify a working directory: ")
    input_directory = batch.Property(".", display="Specify an input directory: ")
    output_directory = batch.Property(".", display="Specify an output directory: ")

    subdirectory = batch.Property(".", verbose = False)
    prior = batch.Property("", verbose = False)    
    post = batch.Property("", verbose = False)    

    nodes = batch.Property(1, display="Nodes: ", verbose = False)    
    cores = batch.Property(1, display="Max cores pr. node: ", verbose = False) 
    memory = batch.Property(128000, display="Memory: ", verbose = False)    
    wall = batch.Property(10, display="Wall time: ", verbose = False)    


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
    hash_input = batch.Function(verbose=True) \
        .entrance().chdir(_).directory_hash(input_directory,True,True) \
        .Qslugify(command).Qjoin(_,"-",_)

    ## TESTED AND WORKING
    identifier_filename = batch.Function() \
        .Qslugify(command).Qstr(overwrite_submission_id).Qjoin(_,"-",_).Qstore("id") \
        .Qstr(overwrite_submission_id).Qequal("",_).Qdo(2).Qcall(hash_input).Qstore("id") \
        .Qget("id").Qjoin(".batchq_",_)


    ## TESTED AND WORKING
    get_subdirectory = batch.Function(verbose=True) \
        .Qstr(subdirectory).Qstore("subdir") \
        .Qequal(_,".").Qdo(3).Qcall(identifier_filename).Qget("id").Qstore("subdir") \
        .Qget("subdir")


    ## TESTED AND WORKING
    create_workdir = batch.Function(verbose=True) \
        .entrance().chdir(_) \
        .exists(working_directory).Qdon(1).mkdir(working_directory, True) \
        .chdir(working_directory) \
        .Qcall(get_subdirectory) \
        .exists(_).Qdon(2).Qget("subdir").mkdir(_, True) \
        .Qget("subdir").chdir(_).pwd().Qstore("workdir")

    ## TODO: TEST
    hash_work = batch.Function(verbose=True) \
        .entrance().chdir(_).directory_hash(output_directory,True,True) \
        .Qslugify(command).Qjoin(_,"-",_)


    ## TESTED AND WORKING
    hash_output = batch.Function(verbose=True) \
        .entrance().chdir(_).directory_hash(output_directory,True,True) \
        .Qdo(3).Qslugify(command).Qjoin(_,"-",_)




    ### TESTED AND WORKING
    prepare_incopy = batch.Function(create_workdir, verbose=True) \
        .entrance().Qpjoin(_,input_directory).Qstore("indir") \
        .Qpjoin(_,"*").Qget("workdir")

    ### TESTED AND WORKING
    prepare_outcopy = batch.Function(create_workdir, verbose=True) \
        .entrance().Qpjoin(_,output_directory).Qstore("outdir") \
        .Qget("workdir").Qpjoin(_,"*").Qget("outdir")


    ### TESTED AND WORKING
    send = batch.Function(prepare_incopy , verbose=True, enduser=True) \
        .cp(_r, _r, True).Qdon(1).Qthrow("Failed to transfer files.")

    ### TESTED AND WORKING
    recv = batch.Function(prepare_outcopy, verbose=True, enduser=True) \
        .cp(_r, _r).Qdon(1).Qthrow("Failed to transfer files.")

    ### TESTED AND WORKING
    pid = batch.Function(create_workdir,verbose=True, enduser=True) \
        .exists(".batchq.pid").Qdon(2).Qstr("-1").Qreturn() \
        .cat(".batchq.pid")


    ### TESTED AND WORKING
    running = batch.Function(pid,verbose=True, enduser=True) \
        .Qstore("pid").Qequal(_,"-1").Qdo(2).Qbool(False).Qreturn() \
        .Qget("pid").isrunning(_)

    ### TESTED AND WORKING
    pending = batch.Function(verbose=True, enduser=True) \
        .Qbool(False)

    ## TODO: THIS SHOULD BE IMPLEMENTED BY TESTING THE EXIT CODE
    failed = batch.Function(verbose=True, enduser=True) \
        .Qbool(False)

    ## TESTED AND WORKING
    submitted = batch.Function(create_workdir,verbose=True, enduser=True) \
        .Qcall(identifier_filename).exists(_)

    ### TESTED AND WORKING
    finished = batch.Function(running,verbose=True, enduser=True) \
        .Qnot(_).Qstore("not_running").Qcall(submitted) \
        .Qget("not_running").Qand(_,_)


    status = batch.Function(verbose=True, enduser=True) \
        .Qcall(running).Qdo(2).Qstr("running").Qreturn() \
        .Qcall(finished).Qdo(2).Qstr("finished").Qreturn() \
        .Qcall(pending).Qdo(2).Qstr("pending").Qreturn() \
        .Qcall(submitted).Qdon(2).Qstr("was not submitted").Qreturn() \
        .Qcall(failed).Qdo(2).Qstr("failed").Qreturn() \
        .Qstr("unknown status")


    ## TESTED AND WORKING
    startjob = batch.Function(create_workdir,verbose=True) \
        .send_command(prior) \
        .Qcall(identifier_filename) \
        .Qjoin("(", command, " > ",_," & echo $! > .batchq.pid )") \
        .send_command(_).Qcall(running)

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


    job = batch.Function(verbose=True, enduser=True) \
        .Qcall(submitted).Qdon(6).Qprint("Uploading input directory.").Qcall(send).Qprint("Submitting job on ").Qcall(startjob).Qstr("").Qreturn() \
        .Qcall(pending).Qdo(3).Qprint("Job is pending.").Qstr("").Qreturn() \
        .Qcall(running).Qdo(3).Qprint("Job is running.").Qstr("").Qreturn() \
        .Qcall(failed).Qdo(3).Qprint("Job has failed:\n\n").Qcall(log).Qreturn() \
        .Qcall(finished).Qdo(4).Qprint("Job has finished.\nRetrieving results.").Qcall(recv).Qstr("").Qreturn() \
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

#    hash_input_directory = batch.Function(verbose=True) \
#        .Qcontroller("local_terminal") \
#        .entrance().chdir(_).directory_hash(NoHUP.input_directory,True,True)

    ## TESTED AND WORKING
    hash_input = batch.Function(verbose=True).Qcontroller("local_terminal") \
        .entrance().chdir(_).directory_hash(NoHUP.input_directory,True,True) \
        .Qdo(2).Qslugify(NoHUP.command).Qjoin(_,"-",_)

    ## TESTED AND WORKING
    hash_output = batch.Function(verbose=True).Qcontroller("local_terminal") \
        .entrance().chdir(_).directory_hash(NoHUP.output_directory,True,True) \
        .Qdo(2).Qslugify(NoHUP.command).Qjoin(_,"-",_,"-",_,"-",_)

    ## TESTED AND WORKING
    prepare_incopy = batch.Function(NoHUP.create_workdir) \
        .Qcontroller("local_terminal") \
        .pwd().Qpjoin(_,NoHUP.input_directory).Qstore("indir")  \
        .Qget("workdir")

    ## TESTED AND WORKING
    prepare_outcopy = batch.Function(NoHUP.create_workdir).Qcontroller("local_terminal") \
        .push_entrance().exists(NoHUP.output_directory).Qdon(1).mkdir(NoHUP.output_directory, True).popd() \
        .entrance().Qpjoin(_,NoHUP.output_directory).Qstore("outdir") \
        .entrance().Qpjoin(_,NoHUP.input_directory).Qstore("indir")  \
        .Qget("outdir").Qget("workdir").Qget("indir")

    ## TESTED AND WORKING
    send = batch.Function(prepare_incopy , verbose=True) \
        .Qcontroller("filecommander").sync(_r,_r, mode = FileCommander.MODE_LOCAL_REMOTE)

    ## TESTED AND WORKING
    recv = batch.Function(prepare_outcopy , verbose=True) \
        .Qcontroller("filecommander").sync(_r,_r, mode = FileCommander.MODE_REMOTE_LOCAL, diff_local_dir =_r)

    
