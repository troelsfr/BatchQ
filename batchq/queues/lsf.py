from batchq.core import batch
from batchq.queues.nohup import NoHUP, NoHUPSSH
from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.utils import FileCommander
from batchq.shortcuts.shell import home_create_dir, send_command

class LSFBSub(NoHUPSSH):
    _1 = batch.WildCard()
    _2 = batch.WildCard()
    _3 = batch.WildCard()

    options = batch.Property("", verbose = False)    


    ## TESTED AND WORKING
    running = batch.Function(NoHUP.pid,verbose=True) \
        .Qjoin("bjobs ",_1," | awk '{ if($1 == ",_2,") {printf $3}}'").send_command(_1) \
        .Qstrip(_1).Qlower(_1).Qequal(_1,"run")

    ## TESTED AND WORKING
    startjob = batch.Function(NoHUP.create_workdir,verbose=True) \
        .send_command(NoHUP.prior) \
        .Qcall(NoHUP.identifier_filename) \
        .Qjoin("(touch ",_1, " && bsub -o ",_2,"_log ", options," \"", NoHUP.command, " > ",_3," \" |  awk '{ if(match($0,/([0-9]+)/)) { printf substr($0, RSTART,RLENGTH) } }' > .batchq.pid )") \
        .send_command(_1)

    ## TESTED AND WORKING   
    finished = batch.Function(NoHUP.pid,verbose=True).Qcontroller("terminal") \
        .Qjoin("bjobs ",_1," | awk '{ if($1 == ",_2,") {printf $3}}' ").send_command(_1) \
        .Qstrip(_1).Qlower(_1).Qequal(_1,"done")

    
    failed = batch.Function(NoHUP.pid,verbose=True).Qcontroller("terminal") \
        .Qjoin("bjobs ",_1," | awk '{ if($1 == ",_2,") {printf $3}}' ").send_command(_1) \
        .Qstrip(_1).Qlower(_1).Qequal(_1,"exit")

    ## TESTED AND WORKING
    pending = batch.Function(NoHUP.pid,verbose=True).Qcontroller("terminal") \
        .Qjoin("bjobs ",_1," | awk '{ if($1 == ",_2,") {printf $3}}' ").send_command(_1) \
        .Qstrip(_1).Qlower(_1).Qequal(_1,"pend")

    ## TODO: write this function
    cancel = batch.Function().Qstr("TODO: This function needs to be implemented")

    ## TESTED AND WORKING
    log = batch.Function(NoHUP.create_workdir,verbose=True) \
        .Qcall(NoHUP.identifier_filename) \
        .Qjoin("cat ",_1,"_log").Qcontroller("terminal") \
        .send_command(_1)
