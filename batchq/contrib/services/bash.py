from batchq.core import batch
from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.sftp import SFTPTerminal


class SendCommand(batch.BatchQ):
    _ = batch.WildCard()

    directory = batch.Property()
    command = batch.Property()
    terminal = batch.Pipeline(BashTerminal)
    
    create_file = batch.Function() \
        .home().chdir(_) \
        .chdir(directory).send_command(command)

instance = SendCommand("Documents", "echo hello world > hello.txt")
instance.create_file()
