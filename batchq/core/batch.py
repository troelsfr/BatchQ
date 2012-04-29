####################################################################################
# Copyright (C) 2011-2012
# Troels F. Roennow, ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
####################################################################################

import copy
import inspect
import types
import sys
import getpass
import unicodedata
import re

from os import path
from batchq.core.errors import BatchQException,BatchQFunctionException

class BaseField(object):
    """
    The base field is the base class for fields in a BatchQ model.
    """
    __object_counter = 0
    def __init__(self):
        self.__counter__ = BaseField.__object_counter
        BaseField.__object_counter+=1 
        self.__model_field__ = True
        self._replaced_by = None
        self._replaces = None
        self.__field_name__ = ""
        self.__base_model__ = None

    def set_replaced_by(self):
        if self._replaces:
            self._replaces.field_replaced_by(self)
        
    def field_replaced_by(self,field):
        if self._replaces:
            self._replaces.field_replaced_by(field)
        else:
            self._replaced_by = field

    def field_replaces(self, newfield):
        self._replaces = newfield

    @property
    def replacement(self):
        if not self._replaced_by is None:
            return self._replaced_by.replacement
        return self


    def get_name(self):
        return self.__field_name__

    def set_name(self, name):
        self.__field_name__ = name

    name = property(get_name, set_name)


    def get_model(self):
        return self.__base_model__
    def set_model(self, model):
        self.__base_model__ = model
    model = property(get_model, set_model)

    



class Property(BaseField):
    """
    Defines a property of an instance of BatchQ.
    """
    def __init__(self, *args, **kwargs):
        super(Property, self).__init__()
        self.isset = len(args)>0 or 'value' in kwargs.iterkeys()
        self.__set_defaults__(*args, **kwargs)

    def __set_defaults__(self, value = None, password = False, verbose = True, display = "", formatter = None, type = str, invariant = False, generator = None, exporter = None):
        self._formatter = formatter
        self._value = value

        if self._formatter:
            self._value = self._formatter(self._value)

        self.exporter = exporter
        if not self.exporter is None:
            self.exporter.register_field(self)
        self.generator = generator
        if not self.generator is None:
            self.generator.register_field(self)
        self.password = password
        self.verbose = verbose
        self.display = display
        self.isuserset = not verbose
        self._on_modify =None
        self.type = type
        self.invariant = invariant



    def interact(self, reduce_interaction = False):
        if reduce_interaction and not self._value is None: return
        t = type(self._value)

        val = None
        if self.password:
            if self.display == "":
                val = getpass.getpass()
            else:
                val = getpass.getpass(self.display)
        else:
            if self.display == "":
                val = raw_input("Enter a text (no field desciption given): ")
            else:                
                val = raw_input(self.display)

        if not self._value is None:
            self.set(t(val))
        else:
            self.set(val)
        return self.get()


    def initialise(self):
#        if not self._value_from is None and hasattr(self.model, self._value_from):
#            self.value = getattr(self.model, self._value_from)
#            self._userset = True
        return True

    def set(self, val):
        r = self.replacement
        oldval = r.get()
        if r == self:
            self.isset = True
            self.isuserset = True
            if self._formatter:
                self._value = self._formatter(val)
            else:
                self._value = val
        else:
            r.set(val)
        if oldval != val and self._on_modify: self._on_modify()

    def set_on_modify(self, listener):
        self._on_modify = listener

    def get(self):
        r = self.replacement
        if r == self:
            value = self._value
            if callable(value):
                return value()
            return value
        else:
            return r.get()


    


class WildCard(BaseField):
    def __init__(self, select = None, reverse = False, lifo = True):
        super(WildCard, self).__init__()
        self._lifo = lifo
        self._reverse = reverse
        self._wcount = 0
        self._select = select
#        self._results = []

    def register(self, results):
        self._results = results
        self._counter = len(results)-1
#        print "Reset counter"

        
    def get(self):        
#        print "GETTING", self._counter, self._results
        if isinstance(self._select, int):
            if self._select >=0 and self._select<len(self._results):
                if self._reverse:
                    return self._results[len(self._results)-self._select - 1]
                else:
                    return self._results[self._select]
            else:
                return None
            
        ret = None
        if not self._reverse:
            if self._counter >= 0:
                ret =  self._results[self._counter]
#                print "yyy"
                self._counter -= 1
        else:
            if self._counter < len(self._results):
                ret =  self._results[self._counter]
#                print "xxx"
                self._counter += 1
#        print self._results
#        print self._counter, ret 
#        print self
        return ret

    def reset(self, wcount):
#        print "Reseting", self
        self._wcount = wcount
#        print "WCount", wcount
        if self._reverse:
            if self._lifo:
                self._counter = len(self._results) - wcount 
            else:
                self._counter =  0
        else:
            if self._lifo:
                self._counter = len(self._results)-1
            else:
                self._counter = wcount-1

class QCallable(object):
    
    def __init__(self, f):
        self._f = f
        
    def __call__(self,*args, **kwargs):

        return self._f(*args, **kwargs)

class FunctionMessage(object):
    def __init__(self, message, function, code = 0):
        self.message = message
        self.function = function
        self.code = code


import time
class Function(BaseField):
    def __init__(self, inherits = None, verbose = False, enduser=False, cache = 0, type = str, highlevel = False, exporter = None):
        super(Function, self).__init__()
        self._listener = None
        self._verbose_functions = ["Qthrow"]
        self._queue = []
        self._wildcards = []
        self._verbose = verbose
        self._queue_counter = 0
        self._executing = False
        self._store = {}
        self._overall_default = ""
        self.enduser = enduser
        self.cache_timeout = cache
        self._last_run = None
        self._debug = False
        self.type = type
        self.highlevel = highlevel
        self.exporter = exporter
        if not self.exporter is None:
            self.exporter.register_field(self)

        if not inherits is None:
            self._queue += [("Qcall", (inherits,), {},True)]

    def clear_cache(self):
        self._last_run = None


    def __call__(self, *args, **kwargs):
        if not self._last_run is None and time.time() < self._last_run+self.cache_timeout :
            if self._debug:
                self.model._debug_comment("USING CACHE FOR " +self.name + "="+str(self._rets[-1]))
#            print "Cache hit:: ", self._name
            return self            

        if self._debug:
            self.model._debug_call_stack_push(self.name)
#        print "Entering call", self
        self._executing = True
        arguments = dict([("arg%d"%i,args[i]) for i in range(0, len(args))])
        arguments.update(kwargs)


        self._wildcards = []
        for fnc, args, kwargs, selfcall  in self._queue:
            for a in args:
                if isinstance(a, WildCard) and not a in self._wildcards:
                    self._wildcards.append(a.replacement)
            for a in kwargs.itervalues():
                if isinstance(a, WildCard)  and not a in self._wildcards:
                    self._wildcards.append(a.replacement)


        self._rets = []
        for w in self._wildcards:
            w.replacement.register(self._rets)
#        print "Wildcards ", self._wildcards

        self._queue_counter = 0
        self._default = self._overall_default
        while self._queue_counter < len(self._queue):

            try:
                bq = self._pipelines[self._default]
            except KeyError:
                raise BatchQException("Please define a controller before the first function definition. This error typically occurs if you define a function before a controller.")


            fnc, args, kwargs, selfcall  = self._queue[self._queue_counter]
#            print self._queue_counter, "Calling", fnc, args, "on", self._default, bq
#            print self._rets

            self._queue_counter += 1
            nargs = ()
            nkwargs = {}

            if selfcall:
                if self._verbose or (fnc in self._verbose_functions):
                    c = getattr(self, fnc)
                    nargs += (self,)
                else:
                    try:
                        c = getattr(self, fnc)
                        nargs += (self,)
                    except:
                        self._rets.append(None)
                        continue
            else:
                if self._verbose or (fnc in self._verbose_functions):
                    c = getattr(bq,fnc)
                else:
                    try:
                        c = getattr(bq,fnc)
                    except:
                        self._rets.append(None)
                        continue
                

#            print "---"

            for ww in self._wildcards:
                # Counts the number of wild cards in function argument
                w = ww.replacement

                w.register(self._rets)
                wcount = len([a for a in args if a == w]) \
                    + len([a for b,a in kwargs.iteritems() if a == w])
                w.reset(wcount)
           

            # Converting properties into their "real" value
            for a in args:
                if isinstance(a, Property):
                    nargs += (a.replacement.get(),)
                elif isinstance(a, WildCard):
                    nargs += (a.replacement.get(),)
                elif fnc == "Qcall":
                    if hasattr(a, "replacement"):
                        nargs += (a.replacement(),)
                    else:
                        nargs += (a,)
                elif isinstance(a, Function):
                    nargs += (a.replacement().val(),)
                elif callable(a):
                    nargs += (a(),)
                else:
                    nargs += (a,)

            for name, val in kwargs.iteritems():
                ## FIXME:: WHen passing on a dictionary with two or more wildcards the order becomes arbitrary as dictionaries are not ordered
                ## FIX: Use inspect to get an order list of arguments
                if isinstance(val, Property):
                    nkwargs[name] = val.replacement.get()
                elif isinstance(val, WildCard):
                    nkwargs[name] = val.replacement.get()

                elif fnc == "Qcall":
                    if hasattr(val, "replacement"):
                        nkwargs[name] = val.replacement()
                    else:
                        nkwargs[name] = val
                elif isinstance(val, Function):
                    nkwargs[name] = val.replacement().val()
                elif callable(val):
                    nkwargs[name] = (val(),)
                else:
                    nkwargs[name] = val

            def caller():
                if fnc=="Qcall":
                    c(*nargs, **nkwargs)
                else:
                    ret = c(*nargs, **nkwargs)
                    if not ret is None:
                        self._rets.append(ret)

#            print "Executing ", fnc,c, "on", self._default, bq
            if self._verbose or (fnc in self._verbose_functions):
#                print nargs
#                print nkwargs
#                print
                try:
                    caller()
                except:
                    if not fnc in self._verbose_functions:
                        print "In ", self.name, ": element ", self._queue_counter
                        print "Was executing ", fnc,c, "on", self._default, bq                        
                        print nargs
                        print nkwargs
                        print args
                        print kwargs
                    raise
            else:
                try:
                    caller()
                except:
                    self._rets.append(None)
            if self._listener:
                self._listener(fnc, args, kwargs, selfcall, self._rets[-1])

        self._executing = False    
        self._last_run = time.time()
        if self._debug:
            self.model._debug_call_stack_pop(self.name + "=" + str(self._rets[-1]))
        return self


    def __getattribute__(self,name):
        try:
            attr = object.__getattribute__(self, name)
            if isinstance(attr, QCallable) and not self._executing:                
                return self.queue(name, selfcall = True)
            return attr
        except AttributeError:
            # Ensure right behaviour with built-in functions
            if name[0:2] == "__" and name[-2:] == "__":
                return BaseField.__getattribute__(self,name)

        return self.queue(name)


    def queue(self, name = None, selfcall = False):
        if name is None:
            return self._queue

        def queue_arguments(*args, **kwargs):
            self._queue.append((name, args, kwargs, selfcall))
            return self

        return queue_arguments   

    def str(self, var):
        pass

    def register(self, pipelines, default):
        self._pipelines = pipelines
        self._default = default
        self._overall_default = default


    def listener(self, listener):
        self._listener = listener


    def val(self):
        return self._rets[-1]

    def results(self):
        return self._rets

    def variables(self):
        return self._store


    @QCallable
    def Qcontains(self, a,b):
        return a in b


    @QCallable
    def Qdebug_comment(self, msg):
        self.model._debug_comment(msg)
        return None


    @QCallable
    def Qclear_cache(self):
        self.model.clear_cache()
        return None


    @QCallable
    def Qprint(self, *args,**kwargs):
        if len(args) == 1:
            print args[0]
        elif len(kwargs) == 0:
            print " ".join(args)
        else:
            print args, kwargs
        return None
        
    @QCallable
    def Qreturn(self,code=0, *message_parts):
        message = " ".join(message_parts)
        self._queue_counter = len(self._queue)
        if code == 0: return None
        return FunctionMessage(message, code, self.name)

    @QCallable
    def Qdo(self, n = None):
        last = self._rets[-1]
        if last: return None
        if not n is None:
            self._queue_counter += int(n)
#            for i in range(self._queue_counter+int(n)-1, self._queue_counter-1, -1):
#                if i< len(self._queue): self._queue.pop(i)
        return None

    @QCallable
    def Qdon(self, n = None):
        last = not self._rets[-1]
        if last: return None
        if not n is None:
            self._queue_counter += int(n)
#            for i in range(self._queue_counter+int(n)-1, self._queue_counter-1, -1):
#                if i< len(self._queue): self._queue.pop(i)
        return None


    @QCallable
    def Qthrow(self, msg = "", exception = None):
        if exception is None:
            raise BatchQFunctionException(msg)
        else:
            raise exception

    @QCallable
    def Qjoin(self, *args):
        return "".join([a for a in args])

    @QCallable
    def Qpjoin(self, *args):
        return path.abspath(path.join(*args))


    @QCallable
    def Qcall(self, val, n = None):
#        print "Qcall", val
#        print "Results", val.results()
        if n is None:
            self._rets += val.results()
            self._store.update(val.variables())
        else:
            self._rets += val.results()[-n:]
            self._store.update(val.variables())
        #        print "Variables:",val.variables()
        return None

    @QCallable
    def Qstore(self, name):
        self._store[name] = self._rets[-1]       
        return None

    @QCallable
    def Qset(self, name,val = ""):
        self._store[name] = val
        return val


    @QCallable
    def Qhas(self, name):
        return name in self._store


    @QCallable
    def Qget(self, name):
        return self._store[name]

    @QCallable
    def Qcontroller(self, name):
        if name in self._pipelines:
            self._default = name
            return None

        raise BaseException("%s was not declared." % name)
        
    @QCallable
    def Qprint_stack(self):
        print self._rets
        return None

    @QCallable
    def Qbool(self,b):
        return bool(b)

    @QCallable
    def Qand(self,a,b):
        return a and b

    @QCallable
    def Qor(self,a,b):
        return a or b

    @QCallable
    def Qnot(self,a):
        return not a



    _slugify_strip_re = re.compile(r'[^\w\s-]')
    _slugify_hyphenate_re = re.compile(r'[-\s]+')
    @QCallable
    def Qslugify(self, value):
        if not isinstance(value, unicode):
            value = unicode(value)
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = unicode(self._slugify_strip_re.sub('', value).strip().lower())
        return self._slugify_hyphenate_re.sub('-', value)


    @QCallable
    def Qstrip(self, string):
        return str(string).strip()

    @QCallable
    def Qstr(self, something):
        return str(something)

    @QCallable
    def Qint(self, something):
        return int(something)


    @QCallable
    def Qlower(self, string):
        return str(string).lower()

    @QCallable
    def Qequal(self, *args):
        ret = True
        val = args[0]        
        for a in args:
            ret = ret and (a == val)

        return ret

    @QCallable
    def Qpush(self, *args):
        for a in args:
            self._rets.append(a)
        return None

    @QCallable
    def Qpop(self, *args):
        for a in args:
            self._rets.pop(a)
        return None

class ControllerMethodReference(object):
    def __init__(self, controller, field):
        self._controller = controller
        self._fields = [field]

    def __call__(self):
        ins = self._controller.instance
        if ins is None:
            ins = self._controller.initiate()

        for a in self._fields:
            ins = getattr(ins, a)
        return ins

    def __getattribute__(self,name):
        try:
            attr = object.__getattribute__(self, name)
            return attr
        except AttributeError:
            # Ensure right behaviour with built-in functions
            if name[0:2] == "__" and name[-2:] == "__":
                return BaseField.__getattribute__(self,name)

        object.__getattribute__(self, "_fields").append(name)
        return self


class Controller(BaseField):
    def __init__(self, model, *args, **kwargs):
        super(Controller, self).__init__()
        self._model = model
        self._args = args
        self._kwargs = kwargs
        self.instance = None

        if "q_instance" in kwargs:
            self.instance = kwargs["q_instance"]
            del kwargs["q_instance"]

        self._fields = []

    def __call__(self):
        return self._instance()

    def __getattribute__(self,name):
        try:
            attr = object.__getattribute__(self, name)
            return attr
        except AttributeError:
            # Ensure right behaviour with built-in functions
            if name[0:2] == "__" and name[-2:] == "__":
                return BaseField.__getattribute__(self,name)

            inst = object.__getattribute__(self, "instance")
            if not inst is None:
                try:
                    if hasattr(inst, name):
                        return getattr(inst, name)
                except:
                    pass

        return ControllerMethodReference(self, name)


    def initiate(self, instance = None):
        """
        This function initiates the pipeline with the arguments given.
        """

        if not instance is None:
            self.instance = instance

        if not self.instance is None:
            if isinstance(self.instance, self._model):
                return self.instance            
            self.instance = self.instance()
            return self.instance

        nargs = ()
        nkwargs = {}
        for a in self._args:
            if isinstance(a, Property):
                nargs += (a.get(),)
            elif callable(a):
                nargs += (a(),)
            else:
                nargs += (a,)

        for name, val in self._kwargs.iteritems():
            if isinstance(val, Property):
                nkwargs[name] = val.get()
            elif callable(val):
                nkwargs[name]  = val()
            else:
                nkwargs[name] = val
        self.instance = self._model(*nargs, **nkwargs)

        return self.instance


import datetime

class MetaBatchQ(type):
    def __new__(cls, name, bases, dct):
        fields = []
        baseconfiguration = {}

        # Inherithed fields
        for b in bases:
            if hasattr(b, "__new_fields__"):
                fields += [(x,y,) for x,y in b.__new_fields__.iteritems()]    
            if hasattr(b, "__baseconfiguration__"):
                baseconfiguration.update([(x,y,) for x,y in b.__baseconfiguration__.iteritems()])

        fields = dict(fields)

        # Finding new fields
        newfields = [(a,dct[a]) for a in dct.iterkeys() if isinstance(dct[a], BaseField)]
        collect_types = [bool, int, str, float, datetime.timedelta]
        baseconfiguration.update(dict( [(a,dct[a]) for a in dct.iterkeys() if type(dct[a]) in collect_types and not a.startswith("__") ] ) )
        

        for a,b in newfields:
            if a in fields:
                b.field_replaces(fields[a])
                b.__counter__ = fields[a].__counter__

            fields[a] = b
                
        dct['__new_fields__'] = fields
        dct['__baseconfiguration__'] = baseconfiguration
        return type.__new__(cls, name, bases, dct)
 
__debug_counter__ = 0
class BatchQ(object):
    """
    The BatchQ object is the ancestor to a specific BatchQ model.
    """
    __metaclass__ = MetaBatchQ

    def _debug_comment(self, msg):
        global __debug_counter__
        msg = msg[:100]
        msg = msg.replace("\n", "<RET>")
        __debug_counter__ += 1
#        print "SENDING ", "#####" +str(__debug_counter__) + " " + msg
        for pipe in self._pipelines.itervalues():
            pipe.send_command("#####" +str(__debug_counter__) + " " + msg)

    def _debug_call_stack_push(self, fnc):
        global __debug_counter__
        __debug_counter__ += 1
        self._debug_call_stack.append(fnc)
        fnc = fnc[:100]
        msg = " : ".join( self._debug_call_stack )
        msg = msg.replace("\n", "<RET>")

        for pipe in self._pipelines.itervalues():
            pipe.send_command("#####" +str(__debug_counter__) + " " + msg)


    def _debug_call_stack_pop(self, fnc):
        global __debug_counter__
        __debug_counter__ += 1
        self._debug_call_stack.pop()
        fnc = fnc[:100]
        msg = "RETURNING! " +  " : ".join( self._debug_call_stack ) + " (  " + fnc + "  )"
        msg = msg.replace("\n", "<RET>")
        for pipe in self._pipelines.itervalues():
            pipe.send_command("#####" +str(__debug_counter__) + " " + msg)



    def _createProperty(self,n):
        def s(self,val):
            return self.fields[n].set(val)
        def g(self):            
            return self.fields[n].get() if n in self.fields else None

        setattr(self.__class__, n, property( g, s ))

    def __init__(self, *args, **kwargs):
        print "Construction args: ", args
        print "Construction kwargs: ", kwargs
        self._log = []
        self._debug_call_stack = []

        self.fields = copy.deepcopy(self.__class__.__new_fields__)
#        print self.fields

        # Setting up replacements and names
        for name, field in self.fields.iteritems():
            field.set_replaced_by()
            field.name = name

        shell = None
        self._pipelines = {}

        last_pipe = None        

        interactive = True
        reduced = True

        self._settings_args = []
        self._settings_kwargs = {}

        if len(args) > 0:
            if isinstance(args[0], BatchQ):
                object = args[0]
                a, k = object.settings
                self._settings_args = copy.deepcopy(a)
                self._settings_kwargs.update(k)
                kwargs.update({"q_pipelines": object.pipelines})
                args = args[1:]
        print "Initial args: ", self._settings_args
        print "Initial kwargs: ", self._settings_kwargs

        if "q_interact" in kwargs:
            interactive = kwargs['q_interact']
            del kwargs['q_interact']
        if "q_reduce_interaction" in kwargs:
            reduced = kwargs['q_reduce_interaction']
            del kwargs['q_reduce_interaction']
        if "q_pipelines" in kwargs:
            self._pipelines = kwargs['q_pipelines']
            del kwargs['q_pipelines']

        n = len(self._settings_args)
        self._settings_args += args[n:]
        self._settings_kwargs.update(self.__class__.__baseconfiguration__)
        self._settings_kwargs.update(kwargs)

        # Make sure that items are treated in order

        items = [(a,b) for a,b in self.fields.iteritems()]
        items.sort(lambda (a,x),(b,y): cmp(x.__counter__, y.__counter__))


        for name, attr in items:
            attr.model = self
            attr.name = name

        properties =  [(a,b) for (a,b) in items if isinstance(b, Property)]
        minpro = len([b for (a,b) in properties if not b.isset])
        properties_dict = dict(properties)
        self._properties = properties 
        self._functions = [(a,b) for (a,b) in items if isinstance(b, Function)]

        i = 0
        wasset = []

        for name, attr in properties:
            attr.initialise()
            attr.set_on_modify(self.clear_cache)
            if i < len(self._settings_args):
                wasset.append(name)
                attr.set(self._settings_args[i])
                i += 1

        if i < len(args):
            raise TypeError("%s recived %d arguments, but at most %d required." % (self.__class__.__name__, len(args)+ len(kwargs), len(properties)))


        for name, val in self._settings_kwargs.iteritems():
            if not name in wasset:
                if name in properties_dict:
                    properties_dict[name].set(val)
                else:
                    raise TypeError("%s got an unexpected keyword argument '%s'" % (self.__class__.__name__, name))
            else:
                print "Settings"
                print "ARGS",self._settings_args
                print "KWARGS",self._settings_kwargs
                raise TypeError("%s got multiple values for keyword argument '%s'" % (self.__class__.__name__, name))

        allset = True
        for name, attr in properties:
            if not attr.isuserset and interactive:
                self._settings_kwargs[name] = attr.interact(reduced)
            allset = allset and attr.isset
            if not attr.isset:
                print name, "was not set"
        if not allset:
            raise TypeError("%s recived %d arguments, at least one of %d mandatory keywords were not set." % (self.__class__.__name__, len(args)+ len(kwargs), minpro))

        for name, attr in items:
            if name in self._pipelines:
                attr.initiate(self._pipelines[name])
                last_pipe = name
                setattr(self, name, attr)
            elif isinstance(attr, Controller):              
                self._pipelines[name] =  attr.initiate()
                last_pipe = name
                setattr(self, name, attr)
            elif isinstance(attr, Function):
                attr.register(self._pipelines, last_pipe)
                setattr(self, name, attr)


        for name, attr in properties:
            if attr.password and name in self._settings_kwargs:
                del self._settings_kwargs[name]
                self._settings_kwargs[name] = "DELETED FOR SECURITY REASONS"
            self._createProperty(name)

        print "Final args: ", self._settings_args
        print "Final kwargs: ", self._settings_kwargs


    def clear_cache(self):
        for name, attr in self._functions:
            attr.clear_cache()

    def listener(self,listener):
        items = [(a,b) for a,b in self.fields.iteritems() if isinstance(b, Function)]

        for a, b in items:
            b.listener(listener)

    @property
    def settings(self):
        return [self._settings_args,self._settings_kwargs]

    def create_job(self, **kwargs):
        empty_copy = False
        if "q_empty_copy" in kwargs:
            empty_copy = True
            del kwargs["q_empty_copy"]
            kwargs['q_interact'] = False

        kw = copy.deepcopy(self._settings_kwargs)

        kw.update(kwargs)
        kw.update({"q_pipelines": self._pipelines})

        if empty_copy:
            kw = dict([(key,val) for (key,val) in kw.iteritems() if key in self._properties and self._properties[key].invariant])

        ret = self.__class__(**kw)
#        print "OBJ",ret
#        print "FNC",ret.submitted
#        print "PIPELINES:", ret._pipelines
        return  ret


    @property
    def pipelines(self):       
        return self._pipelines

    def pipeline(self,name):       
        """
        Returns the pipeline with controller name ``name``.
        """
        return self._pipelines[name] if name in self._pipelines else None


    @property
    def queue_log(self):       
        return self._log

    def interact(self, all = False):
        """
        This function will ask you to fill in properties that was not
        feld by the contructor or manually through the properties. 
        """
        for name, attr in self._properties:
            if not attr.isuserset or all:
                self._settings_kwargs[name] = attr.interact()

    def _args_to_dict(self, args):
        dct = {}
        i = 0
        for name, attr in properties:
            attr.initialise()
            if i < len(args):
                dct.update({name: args[i]})
                i += 1
        return dct

    def __getattribute__(self,name):

        if hasattr(object, "fields") and  name in object.__getattribute__(self,"fields"):
#        if hasattr(self, "fields") and  name in object.__getattribute__(self,"fields"):
            object.__getattribute__(self,"_log").append(name)

        return object.__getattribute__(self, name)



import json
configurations_directory = path.join(path.dirname(__file__), "..","configurations")
def load_settings(filelist):
    switches = []
    ret_args = []
    ret_kwargs = {}
    for filename in filelist.split(","):
        file = None
        try:
            file = open(filename)
        except:
            pass
        if file is None:
            try:
                home = path.expanduser("~")        
                file = open(path.join(home,".batchq/configurations/",filename))
            except:
                pass

        if file is None:
            try:                
                file = open(path.join(configurations_directory,filename))
            except:
                pass

        if file is None:
                raise BaseException("Configuration '%s' not found" % filename)

        args, kwargs, switches = json.load(file)        
        for n in range(0, len(args)):
            if n<len(ret_args):
                ret_args[n] = args[n]
            else:
                ret_args[n].append(args[n])
        ret_kwargs.update(kwargs)

        file.close()

    return ret_args, ret_kwargs, switches


def load_queue(cls,settings):
    if isinstance(settings, dict):
        args = ()
        kwargs = settings
    elif isinstance(settings, tuple):
        args = settings
        kwargs = {}
    else:
        args, kwargs, switches = load_settings(settings)
        u,t,i,q,f = switches
            
        if i:
            kwargs['q_interact'] = True
    return cls(*args,**kwargs)






class Exportable(object):    
    def __init__(self, f):
        self._f = f
        
    def __call__(self,*args, **kwargs):

        return self._f(*args, **kwargs)



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
        elif isinstance(other, BatchQ):
            self.__append(other)

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
            raise BaseException("Something is wrong")
        return ", ".join([str(r) for r in self._results])
#        return ", ".join([job.identifier().val() for job in self.objects])

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

    @Exportable
    def wait(self, min = -1, max_retries = -1, finish = False, split= False):
        ret = copy.copy(self)
        ret._collect_parameters(min,max_retries,finish, split)
        return ret

    @Exportable
    def split(self):
        return self.wait(self._min,self._max,self._until_finish, True)

    @Exportable
    def any(self):
        return self.wait(1)

    def as_list(self):        
        if self._results is None:
           return [] 
        return self._results

    def as_dict(self):        
        # TODO: implement
        if self._results is None:
           return [] 
# TODO: Implement
#        [job.identifier().val() for job in self.objects]
        return self._results



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

            notstop = True
            allowbreak = not self._until_finish 
            ret2 = copy.copy(self._set)
            ret1 = []            

            results1 = []  

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
                    if hasattr(b,"val"): b = b.val()

                    
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














if __name__ == "__main__":
    import sys
    class TestPipe(object):
        """
        This is the documentation
        """
        __counter__ = 0
        def __init__(self, msg = "Hello world!"):
            self.msg = msg
            self._counter = TestPipe.__counter__
            TestPipe.__counter__ += 1 

        def hello(self):
            print self.msg
            return "Hello return value"

        def func_with_args(self,*args, **kwargs):
            print "FUNC WITH ARGS: ", self._counter, args, kwargs
            return "some function"

        def manyresults(self, ret):
            return ret

        def pwd(self):
            return "PWD Value"

        def home(self):
            return "home Value"

        def other(self):
            return "other Value"

        def next(self):
            return "next Value"


    print ""
    print "Model and Function"


    class TestQ(BatchQ):
        _ = WildCard(reverse = False, lifo = True)
        _3 = WildCard(select=2, reverse=False)

        q = Property()
        id = Property("H3ll0 world")
        message = Property("Hello TEST!")


        test = Controller(TestPipe, message)
        x = Function() \
            .hello() \
            .other() \
            .next() \
            .pwd()   \
            .home() \
            .func_with_args(_, secure=_, d=_3) \

        other = Controller(TestPipe, "Hello other")
        y = Function(x) \
            .hello()
        

    blah = TestQ("j", "This is the id",message="New MEssage")
    print "ISSET: ", blah.q
    print blah.message
    print blah.id
    blah2 = TestQ("Hello XXX!")
    class T(object):
        def __init__(self):
            self.i = 0
        def f(self):
            self.i = self.i + 1
            return "Id in a new way %d" % self.i 

    blah.id = T().f
    blah2.id = "Id in a new way II"
    print "Calling blah.x"
    print "--------------"
    blah.x() #fields['x']()
    print "Calling blah.y"
    print "--------------"
    blah.y()

#    print blah.y.queue()
#
#    print "Calling blah2.x"
#    print "--------------"
#    blah2.x() #fields['x']()
#    print "Calling blah2.y"
#    print "--------------"
#    blah2.y() #fields['x']()
