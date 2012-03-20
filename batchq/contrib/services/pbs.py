from batchq.core import batchq
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.sftp import SFTPTerminal
from batchq.contrib import vistrails
from batchq.contrib import commandline


class PBS( batchq.BatchQ ):
    _ = batchq.WildCard()

    username = batchq.Property()
    password = batchq.Property( password = True )
    local = batchq.Property("localhost")
    remote = batchq.Property()

    id = batchq.Property()

    ssh = batchq.Pipeline(SSHTerminal, server, 22, username, password)   

    remote_working = batchq.Function() \
        .pwd()                         \
        .cat(".remotedir")             \
        .pjoin(_,_)                    \   
        .cd(_)                     


    isrunning = batchq.Function(remote_working) \
        .readfile(".pid").isrunning()

    queue = batchq.Function() \
        .str("$remote")       \
        .pjoin("$id")         \
        .cd()                 \
        .send_command("pbs -q $scriptfile")

    cancel = batchq.Function() \

    isqueued = batchq.Function()

    sftp = batchq.Pipeline(SFTPTerminal)     
    push = batchq.Function()
    pull = batchq.Function()

    def submit(self):
        if not self.isrunning():
            self.push()
            self.queue()

        return self

class PBSVistrails( vistrails.Model ):
    __derive_from__ = PBS

class PBSCommand( commandline.Model ):
    __derive_from__ = PBS

class PBSWebModel( django.Model ):
    __derive_from__ = PBS


if __name__ == "__main__":
    import getpass
    passwd = getpass.getpass()
    p = PBS("localhost","tfr",passwd)
    p.
