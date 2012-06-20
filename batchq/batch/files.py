from batchq.core.batch import Shell

## Transfer(whereto, src = ["file", "dir"," file"], dest_dir)
## Transfer(whereto, src = "file", dest_dir)
## Transfer(whereto, src = "dir", dest_dir)

## Copy(terminal, src, dest, symbolic_link, recursive, dereference)
## CreateTemporaryFile( )

## Delete(terminal, dest, recursive, force)

class TransferFiles(Shell):
    def __init__(self, whereto, local_directory = ".", 
                 remote_directory = ".", dependencies = None, 
                 identifier = None, **kwargs):

        self.local_directory = local_directory
        self.remote_directory = remote_directory
        self.whereto = whereto.lower().strip()
        self._was_executed = False
        self._success = False

        super(TransferFiles,self).__init__(None, dependencies = dependencies, 
                                       identifier = identifier,**kwargs)

        self.mode = self.terminal.MODE_LOCAL_REMOTE
        if self.whereto == "local": 
            self.mode = self.terminal.MODE_REMOTE_LOCAL        

    def status(self):
        if self._status == self.STATUS.FINISHED: return self._status
        if self._status == self.STATUS.FAILED: return self._status
        super(TransferFiles, self).status()
        if self._status == self.STATUS.QUEUED: return self._status

        if self._was_executed: 
            if self._success:
                self._status = self.STATUS.FINISHED
            else:
                self._status = self.STATUS.FAILED
        return self._status

    def run(self):
        if self._status == self.STATUS.FINISHED: return self._status
        stat = super(TransferFiles,self).run()

        if stat != self.STATUS.READY: return stat

        self._was_executed = True
        self._success = False
        ret = self.terminal.sync(self.local_directory, 
                                 self.remote_directory,mode = self.mode )
        print "RET", ret
        if not ret is None:
            self._success = True
