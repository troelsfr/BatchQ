from batchq.core.library import Library
from batchq.queues.nohup import NoHUP,NoHUPSSH
from batchq.queues.lsf import LSFBSub
from batchq.queues.functions import create_configuration,list,help, server, client

Library.queues.register("nohup",NoHUP)
Library.queues.register("ssh-nohup",NoHUPSSH)
Library.queues.register("lsf",LSFBSub)
Library.functions.register("configuration",create_configuration)
Library.functions.register("list",list)
Library.functions.register("help",help)

Library.functions.register("server",server)
Library.functions.register("client",client)

