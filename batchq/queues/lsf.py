from batchq.core import batch
from batchq.queues.nohup import NoHUP, NoHUPSSH
from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.utils import FileCommander
from batchq.shortcuts.shell import home_create_dir, send_command


class LSFBSub(NoHUPSSH):
    _1 = batch.WildCard()
    _rev = batch.WildCard(reverse=True)
    _last = batch.WildCard( select = 0, reverse = True)

    lsf_status = batch.Function(NoHUP.pid,verbose=True,cache=5).Qcontroller("terminal") \
        .Qjoin("bjobs ",_last," | awk '{ if($1 == ",_last,") {printf $3}}' ").send_command(_1) \
        .Qstrip(_1).Qlower(_1) 


    ## TESTED AND WORKING
    log = batch.Function(NoHUP.create_workdir,verbose=True, enduser = True) \
        .Qcall(NoHUP.identifier_filename).Qjoin(_1,".log").Qstore("log_file") \
        .isfile(_1).Qdon(2).Qstr("").Qreturn() \
        .Qget("log_file") \
        .Qjoin("cat ",_1).Qcontroller("terminal") \
        .send_command(_1)

    failed = batch.Function(NoHUP.lazy_finished,verbose=True,cache=5).Qcontroller("terminal") \
        .Qdon(2).Qbool(False).Qreturn() \
        .Qcall(log).Qcontains("Successfully completed.",_1) \
        .Qdon(3).Qbool(True).Qreturn() \
        .Qcall(lsf_status).Qequal(_1,"exit")

    ## TESTED AND WORKING
    running = batch.Function(NoHUP.lazy_finished,verbose=True,cache=5) \
        .Qdo(2).Qbool(False).Qreturn() \
        .Qcall(lsf_status).Qequal(_1,"run")

    ## TESTED AND WORKING
    pending = batch.Function(NoHUP.lazy_finished,verbose=True,cache=5).Qcontroller("terminal") \
        .Qdo(2).Qbool(False).Qreturn() \
        .Qcall(NoHUP.lazy_running).Qdo(2).Qbool(False).Qreturn() \
        .Qcall(lsf_status).Qequal(_1,"pend")

    prepare_submission = batch.Function() \
         .Qstr(NoHUP.threads).Qjoin("export  OMP_NUM_THREADS=",_1).send_command(_1) \
         .Qset("command_prepend","").Qbool(NoHUP.mpi).Qdo(3).Qstr(NoHUP.processes).Qjoin("mpirun -np ", _1 , " ").Qstore("command_prepend") \
         .Qstr(NoHUP.processes).Qjoin("-n ", _1 , " ").Qstore("bsub_params") \
         .Qstr(NoHUP.time).Qequal(_1,"-1").Qdon(4).Qget("bsub_params").Qstr(NoHUP.time).Qjoin(_rev, "-W ",_rev, " ").Qstore("bsub_params") \
         .Qstr(NoHUP.memory).Qequal(_1,"-1").Qdon(4).Qget("bsub_params").Qstr(NoHUP.memory).Qjoin(_rev, "-R \"rusage[mem=",_rev,"]\" ").Qstore("bsub_params") \
         .Qstr(NoHUP.diskspace).Qequal(_1,"-1").Qdon(4).Qget("bsub_params").Qstr(NoHUP.diskspace).Qjoin(_rev, "-R \"rusage[scratch=",_rev,"]\" ").Qstore("bsub_params")       

    ## TESTED AND WORKING
    startjob = batch.Function(NoHUP.create_workdir,verbose=True) \
        .Qcall(prepare_submission) \
        .send_command(NoHUP.prior) \
        .Qget("bsub_params") \
        .Qget("command_prepend") \
        .Qcall(NoHUP.identifier_filename, 1) \
        .Qjoin("(touch ",_last, ".submitted ; bsub -oo ", _last, ".log ", _rev," \"touch ",_last,".running ; ", _rev , NoHUP.command, " 1> ",_rev,".running 2> ",_last,".error ; echo \\$? > ",_last,".finished \" |  awk '{ if(match($0,/([0-9]+)/)) { printf substr($0, RSTART,RLENGTH) } }' > ",_last,".pid )") \
        .send_command(_1) \
        .Qclear_cache() 

    ## TODO: write this function
    cancel = batch.Function().Qstr("TODO: This function needs to be implemented")

