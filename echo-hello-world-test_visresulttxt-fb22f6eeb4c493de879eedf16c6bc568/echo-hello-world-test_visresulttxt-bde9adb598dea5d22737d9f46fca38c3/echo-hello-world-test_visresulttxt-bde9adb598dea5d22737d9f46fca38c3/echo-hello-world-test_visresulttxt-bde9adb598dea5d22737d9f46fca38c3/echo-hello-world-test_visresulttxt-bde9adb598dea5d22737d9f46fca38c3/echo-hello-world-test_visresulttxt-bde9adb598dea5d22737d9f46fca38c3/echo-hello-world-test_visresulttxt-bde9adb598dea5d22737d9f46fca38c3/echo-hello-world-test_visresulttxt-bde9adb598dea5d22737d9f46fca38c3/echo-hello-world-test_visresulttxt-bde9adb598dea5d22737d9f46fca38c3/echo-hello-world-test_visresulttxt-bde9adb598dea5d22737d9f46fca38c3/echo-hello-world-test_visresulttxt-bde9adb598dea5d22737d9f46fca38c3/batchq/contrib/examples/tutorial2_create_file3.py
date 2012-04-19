from batchq.core import batch
from batchq.pipelines.shell.bash import BashTerminal
from batchq.shortcuts.shell import home_create_dir, send_command

class CreateFileShort(batch.BatchQ):
    _ = batch.WildCard()
    directory = batch.Property()
    command = batch.Property()

    terminal = batch.Controller(BashTerminal)

    create_dir = home_create_dir(directory,_)
    create_file = send_command(command, inherits = create_dir)
