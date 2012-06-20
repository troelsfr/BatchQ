from batchq.core.library import Library
from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.sftp import SFTPTerminal
from batchq.pipelines.shell.utils import FileCommander

Library.pipelines.register("bash",BashTerminal)
Library.pipelines.register("ssh",SSHTerminal)
Library.pipelines.register("sftp",SSHTerminal)
