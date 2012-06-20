from batchq.core.batch import Shell

## CreateTemporaryDirectory( )
## DeleteDirectory( )

class CreateDirectory(Shell):
    def __init__(self, terminal, directory, working_directory = None, 
                 intermediate=False, dependencies=None, identifier = None,
                 **kwargs):
        self.directory = directory
        self.intermediate =  intermediate
        self._was_executed = False 

        super(CreateDirectory,self).__init__(terminal, working_directory = working_directory, dependencies = dependencies,identifier = identifier,**kwargs)


    def status(self):
        super(CreateDirectory, self).status()
        if self._status == self.STATUS.FINISHED: return self._status
        if self._status == self.STATUS.QUEUED: return self._status

        if self.terminal.isdir(self.directory):
            self._status = self.STATUS.FINISHED
        elif self._was_executed:
            self._status = self.STATUS.FAILED
        return self._status

    def run(self):
        stat = super(CreateDirectory,self).run()
        if stat != self.STATUS.READY: return stat

        self._pushw()
        try:
            self.terminal.mkdir(self.directory, self.intermediate)
            self._was_executed = True
        except:
            self._popw()
            raise
        self._popw()
        return self.status()
