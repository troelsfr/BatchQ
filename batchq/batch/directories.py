from batchq.core.batch import Shell
#from profilehooks import profile
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

#    @profile(immediate=True)
    def run(self):
        super(CreateDirectory,self).run()
        if self.state() != self.STATE.READY: 
            return False
        self._pushw()
        try:
            if self.terminal.mkdir(self.directory, self.intermediate):
                self._state = self.STATE.FINISHED
            self._was_executed = True
        except:
            self._popw()
            raise
        self._popw()
        return True
