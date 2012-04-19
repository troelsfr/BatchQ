from batchq.core.library import Library
from batchq.core import batch
from batchq.pipelines.shell.bash import BashTerminal
from batchq.shortcuts.shell import home_create_dir, send_command

class NoHUPStart(batch.BatchQ):
    _r = batch.WildCard(reverse = True)
    _ = batch.WildCard()

    input_directory = batch.Property()
    working_directory = batch.Property()
    command = batch.Property()

    terminal = batch.Controller(BashTerminal)

    workdir = batch.Function() \
        .home().chdir(_).exists(working_directory) \
        .don(1).mkdir(working_directory).chdir(working_directory)

    _set_copy_dirs = batch.Function(workdir, verbose=False) \
        .pjoin(input_directory, "/*").pjoin(working_directory, "/").cp(_r, _r) \

    transfer_infiles = batch.Function(_set_copy_dirs , verbose=False)
        .cp(_r, _r).don(1).throw("Failed to transfer files.")

    transfer_outfiles = batch.Function(_set_copy_dirs, verbose=False) \
        .cp(_, _).don(1).throw("Failed to transfer files.")

    startjob = batch.Function(workdir) \
        .join("(", command, " > .bacthq.output & echo $! > .batchq.pid )").send_command(_) 

    transfer_startjob = batch.Function(transfer_infiles) \
        .call(startjob)


    getpid = batch.Function(workdir) \
        .cat(".batchq.pid")

    isrunning = batch.Function(get_pid) \
        .isrunning(_)

    wasstarted = batch.Function(workdir) \
        .exists(".batchq.output")

    log = batch.Function(wasstarted) \
        .do(1).cat(".batchq.output")

    clean = batch.Function(wasstarted) \
        .do(1).rm(".batchq.*", force = True)


Library.queues.register("nohup",NoHUPStart)
if __name__=="__main__":
    dir1 = raw_input("Enter a input directory: ")
    dir2 = raw_input("Enter a output directory: ")
    cmd = raw_input("Enter a command: ")
    x = NoHUPStart(dir1, dir2, cmd)
    
    while True:
        x.interact()
#    print "1) Transfer input files"
#    print "2) Submit job"
#    print "3) Transfer input and submit job"

#    print "4) Check if it was started"
#    print "5) Check if it is running"
#    print "6) Transfer output files"
#    print "7) Show log"
#    print "8) Clean up"

#    print "Q) Quit"
#    print ""
#    choice = raw_input("# :")
    
