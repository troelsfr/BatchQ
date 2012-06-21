import time
from batchq.core.batch import Shell
#from batchq.decorators.cache import cacheable
# TODO: Fetch all PIDs at once and make a cache similar to BJOBS

LSF_BJOBS_CACHE = {}

class Subshell(Shell):
    def __init__(self, terminal, command, working_directory=None, dependencies=None,identifier = None, **kwargs):

        self._lsf_cache = "" 
        self._lsf_last_run = None
        self.cache_timeout = 1

        if not hasattr(self,"original_command"):
            self.original_command = command
        self._pid = None
        super(Subshell,self).__init__(terminal, command, working_directory, dependencies,identifier,**kwargs)


        self.command = "".join( ["(touch ",self.identifier_filename, ".submitted ;  touch ",self.identifier_filename,".running ; ( ( ", self.original_command, " ) 1> ",self.identifier_filename,".running 2> ",self.identifier_filename,".error ;  echo $? > ",self.identifier_filename,".finished ) & echo $! > ",self.identifier_filename,".pid )"] )


#TODO: use @cacheable instead
    def pid(self):
        if not self._pid is None: return self._pid
        filename = self.identifier_filename +".pid"
        if not self.terminal.isfile(filename):
            return 0
        n = self.terminal.cat(filename).strip()
        if n=="": return 0
        self._pid = int(n)
        return self._pid

    def state(self):        
        super(Subshell, self).state()
        if self._state == self.STATE.FINISHED: return self._state
        if self._state == self.STATE.FAILED: return self._state
        if self._state < self.STATE.READY: return self._state
        self._pushw()
        try:
            if self.terminal.isfile("%s.failed"%self.identifier_filename): self._state = self.STATE.FAILED
            elif self.terminal.isfile("%s.finished"%self.identifier_filename): self._state = self.STATE.FINISHED
            elif self.terminal.isfile("%s.running"%self.identifier_filename): self._state = self.STATE.RUNNING
            elif self.terminal.isfile("%s.submitted"%self.identifier_filename): self._state = self.STATE.SUBMITTED
#            else:
#                self._state = self.STATE.NOJOB
        except:
            self._popw()
            raise
        self._popw()
        return self._state

class LSF(Subshell):
    def __init__(self, terminal, command, working_directory=None, dependencies=None,identifier = None, **kwargs):

        if not hasattr(self,"original_command"):
            self.original_command = command
        self.additional_arguments = {'processes': 1, 'time': -1, 'mpi': False, 'threads': 1, 'memory':-1, 'diskspace': -1}

        super(LSF,self).__init__(terminal, command, working_directory, dependencies,identifier, **kwargs)
        
        prepend = ""
        if self.additional_arguments['mpi']: prepend = "mpirun -np %d " % self.additional_arguments['processes']

        bsubparams ="-n %d " % self.additional_arguments['processes']
        if self.additional_arguments['time'] !=-1: bsubparams+="".join(["-W ",str(self.additional_arguments['time']), " "])
        if self.additional_arguments['memory'] !=-1: bsubparams+="".join(["-R \"rusage[mem=",str(self.additional_arguments['memory']), "]\" "])
        if self.additional_arguments['diskspace'] !=-1: bsubparams+="".join(["-R \"rusage[scratch=",str(self.additional_arguments['diskspace']), "]\" "])

        self.command = prepend + "".join(["(touch ",self.identifier_filename, ".submitted ; bsub -oo ", self.identifier_filename, ".log ", bsubparams," \"touch ",self.identifier_filename,".running ; ", prepend , self.original_command, " 1> ",self.identifier_filename,".running 2> ",self.identifier_filename,".error ; echo \\$? > ",self.identifier_filename,".finished \" |  awk '{ if(match($0,/([0-9]+)/)) { printf substr($0, RSTART,RLENGTH) } }' > ",self.identifier_filename,".pid &)"])

    def _lsf_state(self):

        global LSF_BJOBS_CACHE
        i = id(self.terminal) 
 
        val = None
        now = time.time()

        if i in LSF_BJOBS_CACHE: 
            to, pval = LSF_BJOBS_CACHE[i]
            if to+self.cache_timeout >= now:
                val =pval
        
        if val is None:
            val = self.terminal.send_command("bjobs -a").strip().lower()
            LSF_BJOBS_CACHE[i] = (now, val)
#        print val
        if val == "no unfinished job found": return ""
        lines = val.split("\n")
        spid = str(self.pid())
#        spid = "374154"
        line = filter(lambda x: x.startswith(spid), lines)
        if len(line)<1: return ""
        blocks = filter(lambda x: x.strip() !="", line[0].split(" "))
#        print "Found ", blocks[2]
        
        return blocks[2].strip()
#        if self._lsf_last_run is None or time.time() > self._lsf_last_run+self.cache_timeout :
#            pid = str(self.pid())
#            cmd = "".join(["bjobs ",pid," | awk '{ if($1 == ",pid,") {printf $3}}' "])
#            self._lsf_last_run = time.time()
#            self._lsf_cache = self.terminal.send_command(cmd).strip().lower()
#        return self._lsf_cache

    def state(self):
        super(LSF, self).state()
        if self._state == self.STATE.FINISHED: return self._state
        if self._state == self.STATE.FAILED: return self._state
        if self._state == self.STATE.QUEUED: return self._state
        if self._state == self.STATE.READY: return self._state
        self._pushw()
        try:
            stat = self._lsf_state()
            if stat == "pend": self._state = self.STATE.PENDING
            elif stat == "run":  self._state = self.STATE.RUNNING
            elif stat == "exit": self._state = self.STATE.FAILED
            elif stat == "done": self._state = self.STATE.FINISHED

        except:
            self._popw()
            raise
        self._popw()
        return self._state
