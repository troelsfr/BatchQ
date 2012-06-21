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


    def state(self):
        super(CreateDirectory, self).state()
        if self._state == self.STATE.FINISHED: return self._state
        if self._state == self.STATE.QUEUED: return self._state

        if self.terminal.isdir(self.directory):
            self._state = self.STATE.FINISHED
        elif self._was_executed:
            self._state = self.STATE.FAILED
        return self._state

    def run(self):
        print "CREATING ", self.directory
        stat = super(CreateDirectory,self).run()
        if stat != self.STATE.READY: return stat

        self._pushw()
        try:
            self.terminal.mkdir(self.directory, self.intermediate)
            self._was_executed = True
        except:
            self._popw()
            raise
        self._popw()
        return self.state()
