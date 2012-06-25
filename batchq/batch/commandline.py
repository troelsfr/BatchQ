import time
import json
from batchq.core.batch import Shell
from batchq.decorators.cache import simple_cacheable, simple_class_cacheable, simple_call_cache, clear_simple_call_cache
# TODO: Fetch all PIDs at once and make a cache similar to BJOBS

LSF_BJOBS_CACHE = {}

class Subshell(Shell):
    def __init__(self, terminal, command, working_directory=None, dependencies=None,identifier = None, **kwargs):


        self.cache_timeout = 1

        if not hasattr(self,"original_command"):
            self.original_command = command
        self._pid = None
        super(Subshell,self).__init__(terminal, command, working_directory, dependencies,identifier,**kwargs)


        self.command = "".join( ["(touch ",self._identifier_filename, ".submitted ;  touch ",self._identifier_filename,".running ; ( ( ", self.original_command, " ) 1> ",self._identifier_filename,".running 2> ",self._identifier_filename,".error ;  echo $? > ",self._identifier_filename,".finished ;  if [ $(cat ",self._identifier_filename,".finished) -ne 0 ] ; then mv ",self._identifier_filename,".finished ",self._identifier_filename,".failed  ;  fi ) & echo $! > ",self._identifier_filename,".pid )"] )


    def _fetch_pids(self):
        # TODO: do this in a clean way 
        cmd = "for f in $(find .batchq*.pid -maxdepth 1 -type f) ; do if [ -s $f ] ; then echo \\\"$f\\\": `cat $f | head -n 1`,; fi ; done"
        pidlst = self.terminal.send_command(cmd).strip()
        if len(pidlst) > 0 and not "no such file or directory" in pidlst.lower():
            json_in = "{"+pidlst[:-1]+"}"
#            print json_in
            try:
                ret = json.loads(json_in)
            except:
                print json_in
                raise
            return  ret
        return {}

    @simple_class_cacheable(5)
    def pid(self):
        path = self.terminal.path

        filename = self._identifier_filename +".pid"
        cid = "fetchpids_%d_%s"%(id(self.terminal),self.terminal.lazy_pwd())
        pid_dict = simple_call_cache(cid, self._identifier, 20, self._fetch_pids)        
        if filename in pid_dict:
            return int(pid_dict[filename])
        return 0


    def _get_files(self):
        ## TODO: make a clean implementation
        if not self._pushw():
            return None
#        print self.terminal.lazy_pwd()
        cmd = "find .batchq.* -maxdepth 1 -type f"
        formatter = lambda x: x[2:len(x)].strip() if len(x) >2 and x[0:2] =="./" else x.strip()
        files = [formatter(x) for x in \
                     self.terminal.send_command(cmd).split("\n")]

        self._popw()
        return files


    def state(self):   
        if self._state == self.STATE.FINISHED: return self._state
        super(Subshell, self).state()
        if self._state == self.STATE.FAILED: return self._state
        if self._state < self.STATE.READY: return self._state
        path = self.terminal.path
        cid = "getfiles_%d_%s"%(id(self.terminal),self.terminal.lazy_pwd())
        
        files = simple_call_cache(cid, self._identifier, 20, self._get_files)

        if files is None: 
            clear_simple_call_cache(cid, self._identifier)
            files = {}
        
        if "%s.failed"%self._identifier_filename in files: 
            self._state = self.STATE.FAILED
        elif "%s.finished"%self._identifier_filename in files: 
            self._state = self.STATE.FINISHED
        elif "%s.running"%self._identifier_filename in files: 
            self._state = self.STATE.RUNNING
        elif "%s.pid"%self._identifier_filename in files: 
            self._state = self.STATE.SUBMITTED

        return self._state

    def reset(self):
        self._pushw()
        self.terminal.rm(self._identifier_filename+"*", force=True)
        self._popw()
        super(Subshell,self).reset()

    def update_cache_state(self):
        idt = (id(self.terminal),self.terminal.lazy_pwd())
        cid = "getfiles_%d_%s" % idt
        clear_simple_call_cache(cid, self._identifier)
        cid = "fetchpids_%d_%s" % idt
        clear_simple_call_cache(cid, self._identifier)

    def standard_error(self):
        self._pushw()
        ret = self.terminal.cat("%s.error"%self._identifier_filename)
        self._popw()
        return ret 

    def standard_output(self):
        self._pushw()
        ret = self.terminal.cat("%s.running"%self._identifier_filename)
        self._popw()
        return ret 


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

        self.command = prepend + "".join(["(touch ",self._identifier_filename, ".submitted ; bsub -oo ", self._identifier_filename, ".log ", bsubparams," \"touch ",self._identifier_filename,".running ; ", prepend , self.original_command, " 1> ",self._identifier_filename,".running 2> ",self._identifier_filename,".error ; echo \\$? > ",self._identifier_filename,".finished ;  if [ $(cat ",self._identifier_filename,".finished) -ne 0 ] ; then mv ",self._identifier_filename,".finished ",self._identifier_filename,".failed  ;  fi\" |  awk '{ if(match($0,/([0-9]+)/)) { printf substr($0, RSTART,RLENGTH) } }' > ",self._identifier_filename,".pid )"])

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

    def log(self):
        self._pushw()
        ret = self.terminal.cat("%s.log"%self._identifier_filename)
        self._popw()
        return ret 
