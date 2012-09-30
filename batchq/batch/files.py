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

    def state(self):
        if self._state == self.STATE.FINISHED: return self._state
        if self._state == self.STATE.FAILED: return self._state
        super(TransferFiles, self).state()
        if self._state <= self.STATE.READY: return self._state

        if self._was_executed: 
            if self._success:
                self._state = self.STATE.FINISHED
            else:
                self._state = self.STATE.FAILED
        return self._state

    def run(self):        
        if self._state == self.STATE.FINISHED: 
            return False

        super(TransferFiles,self).run()
        if self.state() != self.STATE.READY: return False

        self._was_executed = True
        self._success = False

        self.local_directory = self.terminal.local.echo(self.local_directory).strip()
        self.remote_directory = self.terminal.remote.echo(self.remote_directory).strip()

        ret = self.terminal.sync(self.local_directory, 
                                 self.remote_directory,mode = self.mode )

        if not ret is None:
            self._success =True
            self._state = self.STATE.FINISHED
        else:
            raise BaseException("Could not syncronise directories '%s' and '%s'. Did you remember to create them?" %(self.local_directory, self.remote_directory))
        return True
