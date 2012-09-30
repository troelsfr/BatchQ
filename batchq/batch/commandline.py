# from profilehooks import profile
import time
import json
from batchq.core.stack import current_machine
from batchq.core.batch import Shell
from batchq.decorators.cache import simple_cacheable, simple_class_cacheable, simple_call_cache, clear_simple_call_cache
import random
# TODO: Fetch all PIDs at once and make a cache similar to BJOBS

LSF_BJOBS_CACHE = {}

class Subshell(Shell):
    def __init__(self, terminal= None, command=None, working_directory=None, dependencies=None,identifier = None, **kwargs):

        self.cache_timeout = 1

        self.machine = current_machine()
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
        ## TODO: Clean up this implementation
        if not self._pushw():
            return None

        ## Getting the output
        filename = ".batchq.tmp.%d" % random.randint(0, 1<< 32)
        path = self.terminal.path.join(self.working_directory, filename)

        cmd = "find .batchq.* -maxdepth 1 -type f > %s" % filename
        self.terminal.send_command(cmd)
        _,lfilename  = tempfile.mkstemp()
        self.machine.getfile(lfilename, path)

        # Getting value
        f = open(lfilename)
        buffer = f.read()
        f.close()
        
        # Cleaining up
        self.machine.remote.rm(filename)
        self.machine.local.rm(lfilename)

        ## storeing contents
        formatter = lambda x: x[2:len(x)].strip() if len(x) >2 and x[0:2] =="./" else x.strip()
        files = [formatter(x) for x in \
                     buffer.split("\n")]

        self._popw()

        return files


#    @profile(immediate=True)
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

import tempfile
class LSFCompressed(Subshell):
    def __init__(self, machine =None):
        
        self.script1 = """#!/bin/bash\n 
source $HOME/.batchq/bin/functions
_internal_load_joblist
echo "Current path"
echo $PWD
echo
"""
        self.script2 = ""

        self.objects =[]
        Shell.__init__(self, terminal = machine)

        self.last_working_directory = None
        self.has_compression = False
        self.is_compressed = True


    def append(self, other):
        if isinstance(other, LSF):
            ## TODO: check if the terminal is the same
            if not other.run_dependencies():
                raise BaseException( "Could not append '%s' since not all dependencies has finished." % str(other) )

            if self.last_working_directory != other.working_directory:
                if not self.last_working_directory is None:
                    self.script1+="\npopd"
                    self.script2+="\npopd"
                self.script1+="\npushd \"%s\""%other.working_directory
                self.script2+="\npushd \"%s\""%other.working_directory
                self.last_working_directory = other.working_directory

        
            self.script1+="\nmark_as_submitted %s"%other.batch_arguments
            self.script2+="\nlsf_submit_job %s"%other.batch_arguments


            self.script2+="\necho hello %d"%len(self.objects)
            self.objects.append(other)
            return self, other
        raise BaseException("Cannot combined LSF jobs with '%s'"%self.__class__.__name__)  


    def pack(self,results):
        if len(results)!= len(self.objects):
            raise BaseException("The number of results must be as large as the number of objects")
        rets = []
        for i in range(0, len(self.objects)):
            rets.append((results[i], self.objects[i]))
        return rets

    def run(self):
        ## TODO: this is far from clean, but it works
        _,filename  = tempfile.mkstemp()

        f= open(filename, "w+")
        f.write(self.script1)
        if not self.last_working_directory is None:
            f.write("\npopd\n\n")

        f.write(self.script2)
        f.write("\n_internal_cleanup")
        if not self.last_working_directory is None:
            f.write("\npopd\n\n")

        f.write("\nrm -rf $0\n\n")
        f.close()

        dest = self.terminal.remote.path.join(self.terminal.remote.home(),"batchq_self_deleting_do_not_touch_%d" % random.randint(0,1<<32))
        self.terminal.sendfile(filename, dest)

        self.terminal.remote.set_permission(dest, "+x")
        self.terminal.remote.send_command("( %s  > %s.log 2>&1 & )" % (dest,dest))

        return [True]*len(self.objects)

class LSF(Subshell):
    def __init__(self, terminal, command, working_directory=None, dependencies=None,identifier = None, **kwargs):


        if not hasattr(self,"original_command"):
            self.original_command = command
        self.additional_arguments = {'processes': 1, 'time': -1, 'mpi': False, 'threads': 1, 'memory':-1, 'diskspace': -1}


        # setting the terminal variables
        self.machine = current_machine()
        super(LSF,self).__init__(terminal, command, working_directory, dependencies,identifier, **kwargs)
        
        prepend = ""
        if self.additional_arguments['mpi']: prepend = "mpirun -np %d " % self.additional_arguments['processes']

        bsubparams ="-n %d " % self.additional_arguments['processes']
        if self.additional_arguments['time'] !=-1: bsubparams+="".join(["-W ",str(self.additional_arguments['time']), " "])
        if self.additional_arguments['memory'] !=-1: bsubparams+="".join(["-R \"rusage[mem=",str(self.additional_arguments['memory']), "]\" "])
        if self.additional_arguments['diskspace'] !=-1: bsubparams+="".join(["-R \"rusage[scratch=",str(self.additional_arguments['diskspace']), "]\" "])

        self.batch_arguments = ". \"%s\" \"%s\" \"%s\" \"%s\""%(self._identifier,self.original_command, prepend,bsubparams)
        self.command = "batchq lsf_submit_job %s"%self.batch_arguments
        self.has_compression = True
        self.is_compressed = False

### TODO: not applicable anymore
#        self.command = prepend + "".join(["rm -rf ", self._identifier_filename,".* && (touch ",self._identifier_filename, ".submitted ; bsub -oo ", self._identifier_filename, ".log ", bsubparams," \"touch ",self._identifier_filename,".running ; ", prepend , self.original_command, " 1> ",self._identifier_filename,".running 2> ",self._identifier_filename,".error ; echo \\$? > ",self._identifier_filename,".finished ;  if [ \\$(cat ",self._identifier_filename,".finished) -ne 0 ] ; then mv ",self._identifier_filename,".finished ",self._identifier_filename,".failed  ;  fi\" |  awk '{ if(match($0,/([0-9]+)/)) { printf substr($0, RSTART,RLENGTH) } }' > ",self._identifier_filename,".pid )"])

    def compress(self, queue):

        c = LSFCompressed(self.machine)
        c.append(self)

        # TODO: sort out compatible types
        for q in queue:
            c.append(q)
        return [], c


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
            # TODO: apply same trick as in _get_files
            val = self.terminal.send_command("bjobs -a").strip().lower()
            LSF_BJOBS_CACHE[i] = (now, val)

        if val == "no unfinished job found": return ""
        lines = val.split("\n")
        spid = str(self.pid())
        line = filter(lambda x: x.startswith(spid), lines)
        if len(line)<1: return ""
        blocks = filter(lambda x: x.strip() !="", line[0].split(" "))
        
        return blocks[2].strip()

    def _get_state(self):
        ## TODO: Delete this function
        # TODO: generalise remote/local stuff

        filename = self.machine.remote.mktemp()
        print "Running:","batchq list_status %s > %s" %(self.working_directory, filename)
        self.machine.remote.send_command("batchq list_status %s > %s" %(self.working_directory, filename))
        
        _,lfilename  = tempfile.mkstemp()
        self.machine.getfile(filename, lfilename)
        self.machine.remote.rm(filename)
        f = open(lfilename)
        contents = f.read()
        f.close()
        print contents
        self.machine.local.rm(lfilename)

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
