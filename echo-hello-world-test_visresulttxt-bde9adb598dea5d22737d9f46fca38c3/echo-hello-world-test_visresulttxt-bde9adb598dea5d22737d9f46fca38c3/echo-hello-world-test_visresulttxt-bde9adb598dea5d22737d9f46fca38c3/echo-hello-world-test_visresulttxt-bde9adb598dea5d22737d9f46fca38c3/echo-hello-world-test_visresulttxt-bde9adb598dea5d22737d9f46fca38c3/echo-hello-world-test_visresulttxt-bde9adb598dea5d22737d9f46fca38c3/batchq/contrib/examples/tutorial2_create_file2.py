from batchq.core import batch
from batchq.pipelines.shell.bash import BashTerminal

class CreateFileAndDirectory(batch.BatchQ):
    _ = batch.WildCard()
    directory = batch.Property()
    command = batch.Property()

    terminal = batch.Controller(BashTerminal)

    create_dir = batch.Function() \
        .home().chdir(_) \
        .exists(directory).Qdon(1).mkdir(directory, True) \
        .chdir(directory)
    
    create_file = batch.Function(create_dir) \
        .send_command(command)
