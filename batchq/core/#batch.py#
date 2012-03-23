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
        self._isset = len(args)>0 or 'value' in kwargs.iterkeys()
        self.__set_defaults__(*args, **kwargs)

    def __set_defaults__(self, value = None, password = False, verbose = True, display = "", value_from = None):
        self._value_from = value_from
        self._value = value
        self._password = password
        self._verbose = verbose
        self._display = display
        self._userset = not verbose

    def interact(self):
        t = type(self._value)

        val = None
        if self._password:
            if self._display == "":
                val = getpass.getpass()
            else:
                val = getpass.getpass(self._display)
        else:
            if self._display == "":
                val = raw_input("Enter a text (no field desciption given): ")
            else:
                val = raw_input(self._display)

        if not self._value is None:
            self.set(t(val))
        else:
            self.set(val)
        return self.get()

    @property
    def fetch_value_from(self):
        return self._value_from

    def initialise(self):
        if not self._value_from is None and hasattr(self.model, self._value_from):
            self.value = getattr(self.model, self._value_from)
            self._userset = True
        return True

    def set(self, val):
        r = self.replacement
        if r == self:
            self._isset = True
            self._userset = True
            self._value = val
        else:
            r.set(val)
        
    def get(self):
        r = self.replacement
        if r == self:
            value = self._value
            if callable(value):
                return value()
            return value
        else:
            return r.get()

    @property
    def isset(self):
        return self._isset

    @property
    def isuserset(self):
        return self._userset

    @property
    def password(self):
        return self._password

    @property
    def verbose(self):
        return self._verbose

    @property
    def display(self):
        return self._display

    


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

class Function(BaseField):
    def __init__(self, inherits = None, verbose = False, enduser=False):
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
        self._intended_for_users = enduser
        if not inherits is None:
            self._queue += [("Qcall", (inherits,), {},True)]

    @property
    def enduser(self):
        return self._intended_for_users

    def __call__(self, *args, **kwargs):
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
                raise BatchQException("Please define a controller before the first function definition.")


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
                    nargs += (a.replacement(),)
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
                    nkwargs[name] = val.replacement()
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
    def Qprint(self, *args,**kwargs):
        if len(args) == 1:
            print args[0]
        else:
            print args, kwargs
        return None
        
    @QCallable
    def Qreturn(self):
        self._queue_counter = len(self._queue)

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

#    @QCallable
#    def Qset(self, name,val):
#        self._store[name] = ""
#        return ""


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

class ControllerReference(object):
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

        self._fields.append(name)
        return self


class Controller(BaseField):
    def __init__(self, model, *args, **kwargs):
        super(Controller, self).__init__()
        self._model = model
        self._args = args
        self._kwargs = kwargs
        self._instance = None

        if "q_instance" in kwargs:
            self._instance = kwargs["q_instance"]
            del kwargs["q_instance"]

        self._fields = []

    def __call__(self):
        return self._instance

    def __getattribute__(self,name):
        try:
            attr = object.__getattribute__(self, name)
            return attr
        except AttributeError:
            # Ensure right behaviour with built-in functions
            if name[0:2] == "__" and name[-2:] == "__":
                return BaseField.__getattribute__(self,name)

        return ControllerReference(self, name)


    def initiate(self):
        """
        This function initiates the pipeline with the arguments given.
        """
        if self._instance:
            if isinstance(self._instance, self._model):
                return self._instance
            return self._instance()

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
        self._instance = self._model(*nargs, **nkwargs)
        return self._instance

    @property
    def instance(self):
        return self._instance



class MetaBatchQ(type):
    def __new__(cls, name, bases, dct):
        fields = []

        # Inherithed fields
        for b in bases:
            if hasattr(b, "__new_fields__"):
                fields += [(x,y,) for x,y in b.__new_fields__.iteritems()]
        fields = dict(fields)

        # Finding new fields
        newfields = [(a,dct[a]) for a in dct.iterkeys() if isinstance(dct[a], BaseField)]


        for a,b in newfields:
            if a in fields:
                b.field_replaces(fields[a])
                b.__counter__ = fields[a].__counter__

            fields[a] = b
                
        dct['__new_fields__'] = fields

        return type.__new__(cls, name, bases, dct)
 

class BatchQ(object):
    """
    The BatchQ object is the ancestor to a specific BatchQ model.
    """
    __metaclass__ = MetaBatchQ

    def _createProperty(self,n,alt_n = None):
        def s(self,val):
            return self.fields[n].set(val)
        def g(self):            
            return self.fields[n].get() if n in self.fields else None

        setattr(self.__class__, n, property( g, s ))
        if not alt_n is None:
            setattr(self.__class__, alt_n, property( g, s ))

    def __init__(self, *args, **kwargs):
        self._log = []

        self.fields = copy.deepcopy(self.__class__.__new_fields__)
        
        # Setting up replacements and names
        for name, field in self.fields.iteritems():
            field.set_replaced_by()
            field.name = name

        shell = None
        self._pipelines = {}

        last_pipe = None        

        interactive = False
        if "q_interact" in kwargs:
            interactive = kwargs['q_interact']
            del kwargs['q_interact']


        self._settings_args = copy.deepcopy(args)
        self._settings_kwargs = copy.deepcopy(kwargs)

        # Make sure that items are treated in order

        items = [(a,b) for a,b in self.fields.iteritems()]
        items.sort(lambda (a,x),(b,y): cmp(x.__counter__, y.__counter__))


        for _, attr in items:
            attr.model = self
        
        properties = [(a,b) for (a,b) in items if isinstance(b, Property)]
        minpro = len([b for (a,b) in properties if not b.isset])
        properties_dict = dict(properties)
        self._properties = properties 

        i = 0
        wasset = []

        for name, attr in properties:
            attr.initialise()
            if i < len(args):
                wasset.append(name)
                attr.set(args[i])
                i += 1

        if i < len(args):
            raise TypeError("%s recived %d arguments, but at most %d required." % (self.__class__.__name__, len(args)+ len(kwargs), len(properties)))


        for name, val in kwargs.iteritems():
            if not name in wasset:
                if name in properties_dict:
                    properties_dict[name].set(val)
                else:
                    raise TypeError("%s got an unexpected keyword argument '%s'" % (self.__class__.__name__, name))
            else:
                raise TypeError("%s got multiple values for keyword argument '%s'" % (self.__class__.__name__, name))

        allset = True
        for name, attr in properties:
            if not attr.isuserset and interactive:
                self._settings_kwargs[name] = attr.interact()
            allset = allset and attr.isset
        
        if not allset:
            raise TypeError("%s recived %d arguments, at least one of %d mandatory keywords were not set." % (self.__class__.__name__, len(args)+ len(kwargs), minpro))

        for name, attr in items:
            if isinstance(attr, Controller):              
                self._pipelines[name] =  attr.initiate()
                last_pipe = name
            elif isinstance(attr, Function):
                attr.register(self._pipelines, last_pipe)
                setattr(self, name, attr)
            elif isinstance(attr, Property):
                self._createProperty(name, attr.fetch_value_from)


    def listener(self,listener):
        items = [(a,b) for a,b in self.fields.iteritems() if isinstance(b, Function)]

        for a, b in items:
            b.listener(listener)

    @property
    def settings(self):
        return [self._settings_args,self._settings_kwargs]

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

        if hasattr(self, "fields") and  name in object.__getattribute__(self,"fields"):
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




class MetaDescriptorQ(type):
    def __new__(cls, name, bases, dct):
        fields = {}

        # Inherithed fields
        for b in bases:
            if hasattr(b, "__baseconfiguration__"):
                fields.update(getattr(b, "__baseconfiguration__"))

        # Finding new fields
        reserved = ["get_queue","update_configuration","queue_log"]
        newfields = dict([(a,dct[a]) for a in dct.iterkeys() if not a in reserved and (len(a) < 4 or (not "__" == a[0:2] and not "__" == a[-2:] )) ])
        fields.update(newfields)
                
        dct['__baseconfiguration__'] = fields

        return type.__new__(cls, name, bases, dct)


class DescriptorQ(object):
    __metaclass__ = MetaDescriptorQ
    def __init__(self, object = None, **kwargs): #          
        queue = None
        if isinstance(object, DescriptorQ):
            queue = object.get_queue()
        elif isinstance(object, BatchQ):
            queue = object

        self._log = []
        configuration = None
        if 'configuration' in kwargs:
            configuration = kwargs['configuration']
        elif len(kwargs) > 0:
            configuration = kwargs

        self._queue = queue
        self._configuration = {}
        self._configuration.update( self.__baseconfiguration__ )

        if isinstance(configuration, str):
            _,configuration,_ = load_settings(configuration)

        if not configuration is None: self._configuration.update(configuration)

        self._queue_cls = None
        if self._queue is None :
            if "queue" in self._configuration:
                self._queue_cls = self._configuration['queue']
                del self._configuration['queue']
            else:
                raise BaseException("You need to provide a queue in order to create a queue descriptor.")

        if not configuration is None:
            if isinstance(configuration, str):
                newargs, newkwargs, switches = load_settings(configuration)
                u,t,i,q,f = switches
                if len(args)< len(newargs):
                    for n in range(0,len(args)):
                        newargs[n] = args[n]
                    args = tuple(newargs)
                
                configuration = self._queue._args_to_dict(args)
                configuration.update(newkwargs)

#            self._configuration.update(configuration)

        self._iterconf = self._configuration.iteritems()

    @property
    def queue_log(self):
        return self._queue.queue_log

    @property
    def descriptor_log(self):
        return self._log


    def get_queue(self):
        if self._queue is None :
            conf = {}
            conf.update(self._configuration)
            conf.update({'q_interact': True})
            self._queue = self._queue_cls(**conf)

        for n, val in self._iterconf:
            self._queue.fields[n].set(val)

        return self._queue

    def update_configuration(self, conf = None, **kwargs):
        if not conf is None:
            self._configuration.update(conf)
        self._configuration.update(kwargs)
        self._iterconf = self._configuration.iteritems()

    def __getattribute__(self,name):
        try:
            attr = object.__getattribute__(self, name)
            return attr
        except AttributeError:
            # Ensure right behaviour with built-in and hidden variables functions
            if name[0] == "_":
                return object.__getattribute__(self,name)

        
        fnc = getattr(self.get_queue(), name)
        object.__getattribute__(self,"_log").append(name)
        return fnc().val

## TODO: Needs to be tested
def load_descriptor(cls,settings):
    settings['q_interact'] = True
    q = load_queue(cls,settings)
    del settings['q_interact']
    d= DescriptorQ(q, settings)
    return d

        


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
