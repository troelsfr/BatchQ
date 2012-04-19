from batchq.core import batch
from batchq.pipelines.shell.bash import BashTerminal
from batchq.shortcuts.shell import home_create_dir, send_command

print ""
print "Loading local files"
print ""
class NoHUP(batch.BatchQ):
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

    transfer_infiles = batch.Function(_set_copy_dirs , verbose=False) \
        .cp(_r, _r).don(1).throw("Failed to transfer files.")

    transfer_outfiles = batch.Function(_set_copy_dirs, verbose=False) \
        .cp(_, _).don(1).throw("Failed to transfer files.")

    startjob = batch.Function(workdir) \
        .join("(", command, " > .bacthq.output & echo $! > .batchq.pid )").send_command(_) 

    transfer_startjob = batch.Function(transfer_infiles) \
        .call(startjob)


    getpid = batch.Function(workdir) \
        .cat(".batchq.pid")

    isrunning = batch.Function(getpid) \
        .isrunning(_)

    wasstarted = batch.Function(workdir) \
        .exists(".batchq.output")

    log = batch.Function(wasstarted) \
        .do(1).cat(".batchq.output")

    clean = batch.Function(wasstarted) \
        .do(1).rm(".batchq.*", force = True)

