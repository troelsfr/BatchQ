from batchq.core import batch
from batchq.queues.nohup import NoHUP, NoHUPSSH
from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.utils import FileCommander
from batchq.shortcuts.shell import home_create_dir, send_command


class LSFBSub(NoHUPSSH):
    _1 = batch.WildCard()
    _2 = batch.WildCard()
    _3 = batch.WildCard(reverse=True)
    _4 = batch.WildCard()


    lsf_status = batch.Function(NoHUP.pid,verbose=True,cache=5).Qcontroller("terminal") \
        .Qjoin("bjobs ",_1," | awk '{ if($1 == ",_2,") {printf $3}}' ").send_command(_1) \
        .Qstrip(_1).Qlower(_1)

    ## TODO: Fix the failed command - this information should be extracted from the log
    failed = batch.Function(lsf_status,verbose=True,cache=5).Qcontroller("terminal") \
        .Qequal(_1,"exit")

    ## TESTED AND WORKING
    running = batch.Function(lsf_status,verbose=True,cache=5) \
        .Qequal(_1,"run")


    ## TESTED AND WORKING
    pending = batch.Function(lsf_status,verbose=True,cache=5).Qcontroller("terminal") \
        .Qequal(_1,"pend")


    prepare_submission = batch.Function() \
         .Qstr(NoHUP.threads).Qjoin("export  OMP_NUM_THREADS=",_1).send_command(_1) \
         .Qset("command_prepend","").Qbool(NoHUP.mpi).Qdo(3).Qstr(NoHUP.processes).Qjoin("mpirun -np ", _1 , " ").Qstore("command_prepend") \
         .Qstr(NoHUP.processes).Qjoin("-n ", _1 , " ").Qstore("bsub_params") \
         .Qstr(NoHUP.time).Qequal(_1,"-1").Qdon(4).Qget("bsub_params").Qstr(NoHUP.time).Qjoin(_3, "-W ",_3, " ").Qstore("bsub_params") \
         .Qstr(NoHUP.memory).Qequal(_1,"-1").Qdon(4).Qget("bsub_params").Qstr(NoHUP.memory).Qjoin(_3, "-R \"rusage[mem=",_3,"]\" ").Qstore("bsub_params") \
         .Qstr(NoHUP.diskspace).Qequal(_1,"-1").Qdon(4).Qget("bsub_params").Qstr(NoHUP.diskspace).Qjoin(_3, "-R \"rusage[scratch=",_3,"]\" ").Qstore("bsub_params")
         
         
    ## TESTED AND WORKING
    startjob = batch.Function(NoHUP.create_workdir,verbose=True) \
        .Qcall(prepare_submission) \
        .send_command(NoHUP.prior) \
        .Qget("bsub_params") \
        .Qget("command_prepend") \
        .Qcall(NoHUP.identifier_filename, 1) \
        .Qjoin("(touch ",_1, " && bsub -o ", _2, "_log ", _3," \"", _3 , NoHUP.command, " > ",_3," \" |  awk '{ if(match($0,/([0-9]+)/)) { printf substr($0, RSTART,RLENGTH) } }' > ",_4,".pid )") \
        .send_command(_1)


    ## TODO: write this function
    cancel = batch.Function().Qstr("TODO: This function needs to be implemented")

    ## TESTED AND WORKING
    log = batch.Function(NoHUP.create_workdir,verbose=True) \
        .Qcall(NoHUP.identifier_filename) \
        .Qjoin("cat ",_1,"_log").Qcontroller("terminal") \
        .send_command(_1)
