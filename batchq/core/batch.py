from batchq.core.stack import current_machine
import re
import unicodedata
import copy
import time
_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')
def slugify(value):
    global _slugify_strip_re, _slugify_hyphenate_re
    if not isinstance(value, unicode):
        value = unicode(value)
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)
 

class Shell(object):
    class STATUS:
        NOJOB = 0
        QUEUED = 1
        READY = 2
        SUBMITTED = 3
        PENDING = 4
        RUNNING = 5
        FAILED = 6
        FINISHED = 7

        texts = {NOJOB: 'no job', 
                 QUEUED: 'queued',
                 READY: 'ready',
                 SUBMITTED: 'submitted',
                 PENDING: 'pending',
                 RUNNING: 'running',
                 FAILED: 'failed',
                 FINISHED: 'finished'}

    def __init__(self, terminal = None, command = None, working_directory=None, dependencies=None, identifier = None, exitcode_zero = True, **kwargs):

        if terminal is None:
            terminal = current_machine()
        elif isinstance(terminal, str):
            terminal =getattr(current_machine(), terminal)

        self.working_directory = working_directory
        self.terminal = terminal
        self.command = command

        if hasattr(self,"additional_arguments"):
            self.additional_arguments.update( kwargs )
        else:
            self.additional_arguments = kwargs

        self._status = self.STATUS.NOJOB
        self._stage = 0

        self.dependencies = [] if dependencies is None else dependencies
        self.identifier = self.generate_identifier() if identifier is None else identifier
        self.identifier_filename = ".batchq.%s"%self.identifier

        self._ret = ""
        self._exitcode = -1
        self._was_executed = False
        self.exitcode_zero =  exitcode_zero

        self.status()

        
    def completed(self, count):
        precendor_count = 0
        return len(self.dependencies) + precendor_count

    def generate_identifier(self):
        ## TODO: Extract information from previous dependencies
        ## TODO: maybe make it with MD5 or SHA
        return slugify(self.command)


    def status(self):
        if self._status == self.STATUS.QUEUED:
            self._status = self.STATUS.READY
            for a in self.dependencies:
                if a.status() !=  self.STATUS.FINISHED:
                    self._status = self.STATUS.QUEUED

        if not self.command is None and self._was_executed:
            self._status = self.STATUS.FINISHED

            if self.exitcode_zero and not self._exitcode is None and self._exitcode != 0:
                self._status = self.STATUS.FAILED

        return self._status

    def pid(self):
        return 0

    def run(self, force=False):
        if self._status == self.STATUS.NOJOB: self._status = self.STATUS.QUEUED
        # Waiting for dependencies to finish
        if self.status() == self.STATUS.QUEUED:
            self._status = self.STATUS.READY
            for a in self.dependencies:
                if a.run() != self.STATUS.FINISHED:
                    print a, "not finished", a._status
                    self._status = self.STATUS.QUEUED
            if self.status() == self.STATUS.QUEUED:
                print "EXIT QUEUED"
                return self._status

        # Executing job
        if not self.command is None:
            if self._status < self.STATUS.SUBMITTED or force:
                self._pushw()
                try:
                    print "Running ", self.command
                    self._ret = self.terminal.send_command(self.command)
                    self._exitcode = self.terminal.last_exitcode()
                    self._was_executed = True
                except:
                    self._popw()
                    raise

        return self.status()


    def _pushw(self):
        if not self.working_directory is None:
            self.terminal.pushd(self.working_directory)

    def _popw(self):
        if not self.working_directory is None:
            self.terminal.popd()


    def queued(self):
        return self.status() == self.STATUS.QUEUED

    def ready(self):
        return self.status() == self.STATUS.READY

    def submitted(self):
        return self.status() == self.STATUS.SUBMITTED

    def pending(self):
        return self.status() == self.STATUS.PENDING

    def failed(self):
        return self.status() == self.STATUS.FAILED

    def running(self):
        return self.status() == self.STATUS.RUNNING

    def finished(self):
        return self.status() == self.STATUS.FINISHED


class Subshell(Shell):
    def __init__(self, terminal, command, working_directory=None, dependencies=None,identifier = None, **kwargs):

        self._lsf_cache = "" 
        self._lsf_last_run = None
        self.cache_timeout = 5

        if not hasattr(self,"original_command"):
            self.original_command = command

        super(Subshell,self).__init__(terminal, command, working_directory, dependencies,identifier,**kwargs)

        self.command = "".join( ["(touch ",self.identifier_filename, ".submitted ;  touch ",self.identifier_filename,".running ; ( ( ", self.original_command, " ) 1> ",self.identifier_filename,".running 2> ",self.identifier_filename,".error ;  echo $? > ",self.identifier_filename,".finished ) & echo $! > ",self.identifier_filename,".pid )"] )


    def pid(self):
        filename = self.identifier_filename +".pid"
        if not self.terminal.isfile(filename):
            return 0
        n = self.terminal.cat(filename).strip()
        if n=="": return 0
        return int(n)

    def status(self):        
        super(Subshell, self).status()
        if self._status == self.STATUS.FINISHED: return self._status
        if self._status == self.STATUS.FAILED: return self._status
        if self._status < self.STATUS.READY: return self._status
        self._pushw()
        try:
            if self.terminal.isfile("%s.failed"%self.identifier_filename): self._status = self.STATUS.FAILED
            elif self.terminal.isfile("%s.finished"%self.identifier_filename): self._status = self.STATUS.FINISHED
            elif self.terminal.isfile("%s.running"%self.identifier_filename): self._status = self.STATUS.RUNNING
            elif self.terminal.isfile("%s.submitted"%self.identifier_filename): self._status = self.STATUS.SUBMITTED
#            else:
#                self._status = self.STATUS.NOJOB
        except:
            self._popw()
            raise
        self._popw()
        return self._status

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

    def _lsf_status(self):
        if self._lsf_last_run is None or time.time() > self._lsf_last_run+self.cache_timeout :
            pid = str(self.pid())
            cmd = "".join(["bjobs ",pid," | awk '{ if($1 == ",pid,") {printf $3}}' "])
            self._lsf_last_run = time.time()
            self._lsf_cache = self.terminal.send_command(cmd).strip().lower()
        return self._lsf_cache

    def status(self):
        super(LSF, self).status()
        if self._status == self.STATUS.FINISHED: return self._status
        if self._status == self.STATUS.FAILED: return self._status
        if self._status == self.STATUS.QUEUED: return self._status
        if self._status == self.STATUS.READY: return self._status
        self._pushw()
        try:
            stat = self._lsf_status()
            if stat == "pend": self._status = self.STATUS.PENDING
            elif stat == "run":  self._status = self.STATUS.RUNNING
            elif stat == "exit": self._status = self.STATUS.FAILED
            elif stat == "done": self._status = self.STATUS.FINISHED

        except:
            self._popw()
            raise
        self._popw()
        return self._status

class Job(object):
    def __init__(self,chain, pull_status_from = None):
        self.chain = chain
        if pull_status_from is None:
            self.pull_status = []
        else:
            self.pull_status = pull_status_from

    def status(self):
        return [a.STATUS.texts[a.status()] for a in self.pull_status]

    def queued(self):
        return [a.queued() for a in self.pull_status]

    def ready(self):
        return [a.ready() for a in self.pull_status]

    def submitted(self):
        return [a.submitted() for a in self.pull_status]

    def pending(self):
        return [a.pending() for a in self.pull_status]

    def failed(self):
        return [a.failed() for a in self.pull_status]

    def running(self):
        return [a.running() for a in self.pull_status]

    def finished(self):
        return [a.finished() for a in self.pull_status]

    def run(self):
        self.chain.run()
        return self.status()
class BatchQ:
    pass
