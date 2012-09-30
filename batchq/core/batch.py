from batchq.core.stack import current_machine
# from profilehooks import profile
import re
import unicodedata
import copy
import time
import hashlib
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
    class STATE:
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
        self.verbose = False
        if terminal is None:
            terminal = current_machine()
        elif isinstance(terminal, str):
            self.terminal_name = terminal
            terminal =getattr(current_machine(), terminal)

        self.working_directory = working_directory
        self.terminal = terminal
        self.command = command

        self.has_compression = False
        self.is_compressed = False

        if hasattr(self,"additional_arguments"):
            self.additional_arguments.update( kwargs )
        else:
            self.additional_arguments = kwargs

        self._state = self.STATE.NOJOB

        self.dependencies = [] if dependencies is None else dependencies
        self._identifier = self.generate_identifier() if identifier is None else identifier
        self._identifier_filename = ".batchq.%s"%self._identifier

        self._ret = ""
        self._exitcode = -1
        self._was_executed = False
        self.exitcode_zero =  exitcode_zero

#        self.state()

    def compress(self, queue):
        raise BaseExepction("Object has no compression.")


    def identifier(self):
        return self._identifier
        
    def completed(self, count):
        precendor_count = 0
        return len(self.dependencies) + precendor_count

    def generate_identifier(self):
        ## TODO: Extract information from previous dependencies
        ## TODO: maybe make it with MD5 or SHA
        m = hashlib.md5()
        if self.command is None:
            return "unkown"
        m.update(self.command)
        return m.hexdigest() #slugify()


    def status(self):
        return self.STATE.texts[self.state()]

#    @profile
    def state(self):
        if self._state == self.STATE.QUEUED:
            self._state = self.STATE.READY
            for a in self.dependencies:
                if a.state() !=  self.STATE.FINISHED:
                    self._state = self.STATE.QUEUED

        if not self.command is None and self._was_executed:
            self._state = self.STATE.FINISHED

            if self.exitcode_zero and not self._exitcode is None and self._exitcode != 0:
                self._state = self.STATE.FAILED

        return self._state

    def pid(self):
        return 0

    def reset(self):
        self._state = self.STATE.NOJOB
        self.update_cache_state()


    def update_cache_state(self):
        pass

#    @profile
    def run_dependencies(self):
        if self._state == self.STATE.NOJOB: self._state = self.STATE.QUEUED
        # Waiting for dependencies to finish

        if self.state() == self.STATE.QUEUED:
            self._state = self.STATE.READY
            for a in self.dependencies:
                a.run()
                if a.state() != self.STATE.FINISHED:
                    self._state = self.STATE.QUEUED

            if self._state == self.STATE.QUEUED:
                print self, "EXIT QUEUED", self.dependencies
                return False
        return True

    def run(self, force=False):
        if not self.run_dependencies(): return False

        # Executing job
        if not self.command is None:
   
            if self._state == self.STATE.READY or force:
                if not self._pushw():
                    raise BaseException("Could not enter working directory: '%s' from '%s' ('%s'). The executed class is '%s'." %(self.working_directory, self.terminal.pwd(), self.terminal.lazy_pwd(),self.__class__.__name__) )
                try:
                    if self.verbose:
                        print "$ ", self.command
                    self._ret = self.terminal.send_command(self.command)
                    self._exitcode = self.terminal.last_exitcode()
                    self._was_executed = True
                except:
                    self._popw()
                    raise
                self._popw()
                self.update_cache_state()
            else:
                return False
        return True

    def _pushw(self):
        self._can_pop = False
        if not self.working_directory is None and \
                self.working_directory.strip() != "." and \
                not self.terminal.lazy_pwd().endswith(self.working_directory):
            self._can_pop = True
            return self.terminal.pushd(self.working_directory)
        return True

    def _popw(self):
        if self._can_pop and \
                not self.working_directory is None and \
                self.working_directory.strip() != ".":
            self.terminal.popd()            
            return True
        return False

    def queued(self):
        return self.state() == self.STATE.QUEUED

    def ready(self):
        return self.state() == self.STATE.READY

    def submitted(self):
        return self.state() == self.STATE.SUBMITTED

    def pending(self):
        return self.state() == self.STATE.PENDING

    def failed(self):
        return self.state() == self.STATE.FAILED

    def running(self):
        return self.state() == self.STATE.RUNNING

    def finished(self):
        return self.state() == self.STATE.FINISHED

    def standard_error(self):
        raise BaseException("Standard error and output are not defined for the shell object. It might be in the future, however, until then use Shell.terminal.buffer")

    def standard_output(self):
        raise BaseException("Standard error and output are not defined for the shell object. It might be in the future, however, until then use Shell.terminal.buffer")

    def log(self):
        raise BaseException("'log' is not defined for the shell object. It is a place holder for the log in LSF and other submission systems.")

## TODO: Delete, since it is not used
class Job(object):
    def __init__(self,chain, pull_state_from = None):
        self.chain = chain
        if pull_state_from is None:
            self.pull_state = []
        else:
            self.pull_state = pull_state_from


    def state(self):
        return [a.STATE.texts[a.state()] for a in self.pull_state]

    def queued(self):
        return [a.queued() for a in self.pull_state]

    def ready(self):
        return [a.ready() for a in self.pull_state]

    def submitted(self):
        return [a.submitted() for a in self.pull_state]

    def pending(self):
        return [a.pending() for a in self.pull_state]

    def failed(self):
        return [a.failed() for a in self.pull_state]

    def running(self):
        return [a.running() for a in self.pull_state]

    def finished(self):
        return [a.finished() for a in self.pull_state]

    def run(self):
        self.chain.run()
        return self.state()



class Collection(object):
           
    def __init__(self, set = None,results_set = None,complement = None,results_complementary=None):
        self._set = [] 
        if not set is None:
            self._set = set

        self._results =[]
        if not results_set is None:
            self._results = results_set
        else:
            self._results = [None]*len(self._set)

        if len(self._results) != len(self._set):
            raise BaseException("Set list and result list must be equally long")

        self._complementary = []
        if not complement is None:
            self._complementary = complement

        self._results_complementary = []
        if not results_complementary is None:
            self._results_complementary = results_complementary
        else:
            self._results_complementary = [None]*len(self._complementary)

        if len(self._results_complementary) < len(self._complementary):
            self._results_complementary += [None]*( len(self._complementary) - len(self._results_complementary) )
        if len(self._results_complementary) != len(self._complementary):
            raise BaseException("Complementary set list and result list must be equally long")


        self._min = -1
        self._max = 1
        self._until_finish = True
        self._split_results = False

    def all(self):
        return self + ~self
        
    @property
    def objects(self):
        return self._set

    @property
    def complementary_objects(self):
        return self._complementary
  
    @property
    def results(self):
        return self._results

    @property
    def complementary_results(self):
        return self._results_complementary

    def __append(self, object, ret = None):
        if object in self._set:
            return
        if object in self._complementary:
            #TODO: delete this object from complementary
            pass
        self._set.append(object)
        self._results.append(ret)

    def __append_complementary(self, object, ret = None):
        if object in self._set or object in self._complementary:
            return
        self._complementary.append(object)
        self._results_complementary.append(ret)


    def __len__(self):
        return len(self._set)

    def __iadd__(self, other):

        if isinstance(other, Collection):
            # Adding objects
            n = len(other.objects)
            for i in range(0, n):
                self.__append(other.objects[i], other.results[i])
                
            # and complementary objects
            n = len(other.complementary_objects)
            for i in range(0, n):
                self.__append_complementary(other.complementary_objects[i], other.complementary_results[i])
        elif isinstance(other, Shell):
            self.__append(other)
        else:
            raise BaseException("Cannot add type '%s' to %s." % (str(type(other)), self.__class__.__name__ ))
        return self

    def __add__(self, other):
        ret = Collection()
        ret.__iadd__(self)
        ret.__iadd__(other)
        return ret

    def __delitem__(self, n):
        del self._set[n]

    def __getitem__(self, n):        
        x = self._set[n]
        if not isinstance(x, list): x = [x]
        return Collection(x)

    def invert(self):
        t = self._set
        r = self._results
        self._set = self._complementary 
        self._results = self._results_complementary 
        self._complementary = t
        self._results_complementary = r

    def __nonzero__(self):
        return len(self._set) != 0

    def __str__(self):
        if len(self._results) != len(self._set):
            raise BaseException("Somebody has been tampering with the set/results.")
        return ", ".join([str(r) for r in self._results])

    def __invert__(self):
        x = copy.copy(self)
        x.invert()
        return x
        
    def __neg__(self):
        return ~ self   

    def _collect_parameters(self, min,max,finish, split = False):
        self._min = min
        self._max = max
        self._until_finish = finish
        self._split_results = split

 
    def select(self, *identifiers):
        newset,newret = [],[]
        comset,comret = [],[]
        for obj in self._set:
            q = obj.identifier()
            if q in identifiers:
                newset.append(obj)
                newret.append(q)
            else:
                comset.append(obj)
                comret.append(q)
        return Collection(newset, newret, comset, comret)

    def as_list(self):        
        if self._results is None:
           return [] 
        return self._results

    def as_dict(self):        
        # TODO: implement
        if self._results is None:
           return [] 
        # TODO: Implement
        return self._results


    def compressed_invoke(self,name):
        try:
            attr = object.__getattribute__(self, name)
            return attr
        except AttributeError:
            if name[0] == "_":
                return object.__getattribute__(self,name)


        def invoke(*args, **kwargs):
            if len(self._set) ==0:
                raise BaseException("Cannot operate on empty set.")

            queue = copy.copy(self._set)
            element = queue[0]
            queue = queue[1:]

            results1 = []
            results2 = []
            while not element is None:
                former = element

                if not element.run_dependencies():
                    ret = False
                else:
                    # Compressing element if possible                    
                    if element.has_compression:
                        queue, element = element.compress(queue)

                    method = getattr(element,name)
                    ret = method(*args, **kwargs)

                if not element.is_compressed:
                    rets_elements = [(ret, element)]
                else:
                    rets_elements = element.pack(ret)

                for ret, element in rets_elements:
                    if ret:
                        results1.append(element)
                    else:
                        results2.append(element)

#                print "Clearing cache"
#                former._pushw()
                former.update_cache_state()
#                former._popw()
                if len(queue)>0: 
                    element = queue[0]
                    queue = queue[1:]
                else:
                    element = None

        return invoke
    ### 
    # deprecated stuff
    def wait(self, min = -1, max_retries = -1, finish = False, split= False):
        ret = copy.copy(self)
        ret._collect_parameters(min,max_retries,finish, split)
        return ret

    def split(self):
        return self.wait(self._min,self._max,self._until_finish, True)

    def any(self):
        return self.wait(1)

    def __getattribute__(self,name):
        try:
            attr = object.__getattribute__(self, name)
            return attr
        except AttributeError:
            # Ensure right behaviour with built-in and hidden variables functions
            if name[0] == "_":
                return object.__getattribute__(self,name)

        def foreach(*args, **kwargs):
            ret1 = []
            ret2 = []
            i = 0
            j = 0
            progress_fnc = None
            if "progress" in kwargs:
                progress_fnc = kwargs['progress']
                del kwargs['progress']
            min = self._min
            max = self._max

            if not min is None and min < 0: min += 1 + len(self._set)

            allowbreak = not self._until_finish 
            ret2 = copy.copy(self._set)
            ret1 = []            
            notstop = len(ret2) >0

            results1 = []  
            results2 = []  

            infinity_wait = 10000
            while notstop:
                results2 = []
                cycle = 0
                cycle_size = len(ret2)
                wait =  infinity_wait
                for a in ret2 :
                    cycle += 1
                    method = getattr(a, name)
                    b = method(*args, **kwargs)


                    
                    to = method.cache_timeout if hasattr(method, "cache_timeout") else infinity_wait
                    if to < wait: wait =to

                    if not b:
                        results2.append(b)
                    else:
                        i += 1                        
                        ret1.append(a)    
                        results1.append(b)       
                        if not min is None and min<=i: 
                            if progress_fnc:
                                progress_fnc(i,min,cycle,cycle_size, j,b,a) 
                            notstop = False
                            if allowbreak: break

                    if progress_fnc:
                        progress_fnc(i,min,cycle,cycle_size, j,b,a) 
                j += 1
                if not max == -1 and j >= max:
                    notstop = False

                if notstop and wait != infinity_wait:
                    time.sleep(wait)

                ret2 = [a for a in ret2 if not a in ret1] 


            col = Collection(ret1, results1, ret2, results2)
            if self._split_results: return col, ~col
            return col
                    
        return foreach
