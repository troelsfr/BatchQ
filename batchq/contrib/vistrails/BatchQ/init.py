from core.modules.vistrails_module import Module, ModuleError, NotCacheable, InvalidOutput, ModuleSuspended
from batchq.core.batch import BatchQ, Function, Property
from batchq import queues
import copy
typeconversion = {str:'(edu.utah.sci.vistrails.basic:String)', bool:'(edu.utah.sci.vistrails.basic:Boolean)', int:'(edu.utah.sci.vistrails.basic:Integer)', float:'(edu.utah.sci.vistrails.basic:Float)'}
qlist = [(a, getattr(queues,a)) for a in dir(queues) if isinstance(getattr(queues,a),type) and issubclass(getattr(queues,a),BatchQ) ]
capitalise = lambda x: x[0].upper() + x[1:].lower()

class Machine(Module):
    get_kwargs = lambda self, cls: dict([(a[0],self.getInputFromPort(a[0])) for a in self._input_ports if self.hasInputFromPort(a[0]) 
                                         and hasattr(cls,a[0]) and isinstance(getattr(cls,a[0]),Property)]).update({'q_interact': False})  

_modules = [Machine]


def machine_compute(self):
    kwargs = self.get_kwargs(self.queue_cls)
    inherits = self.getInputFromPort('inherits').queue if self.hasInputFromPort('inherits') else None
# TODO: Implement    if not self.queue is None: self.queue.disconnect()
    self.queue = self.queue_cls(kwargs) if inherits is None else self.queue_cls(inherits, kwargs) 
    self.setResult("machine", self)

job_properties = {}
operations = {}
operations_types = {}
for name, queue in qlist:
    properties = []
    for a in dir(queue):
        if isinstance(getattr(queue,a), Property):
            attr = getattr(queue,a)
            if attr.verbose and attr.invariant:
                properties.append( (a,typeconversion[attr.type])  )
            if not attr.password and not attr.invariant:
                job_properties[a] = (a,typeconversion[attr.type],not attr.verbose)
    members = { '_input_ports' : properties + [('inherits','(edu.ethz.sci.vistrails.batchq:Machine)',True)], 'queue_cls': queue,
                '_output_ports': [('machine', '(edu.ethz.sci.vistrails.batchq:Machine)')],
                'compute': machine_compute, 'queue':None}
    cls = type('Machine'+name[0].upper()+name[1:].lower(), (Machine,), members)

    functions = [(a,getattr(queue,a).type) for a in dir(queue) if isinstance(getattr(queue,a), Function) and not a.startswith("_") and getattr(queue,a).enduser]
    for f, t in functions:
        if not f in operations:
            operations[f] = []
            operations_types[f] = []
        operations[f].append(name)
        if not t in operations_types[f]: operations_types[f].append(t)

    _modules.append(cls)

class Job(Machine):
    _input_ports = [('job', '(edu.ethz.sci.vistrails.batchq:Job)'),]
    _output_ports = [b for b in job_properties.itervalues()]
    
    def compute(self):
        self.setResult("job", self)        

class PrepareJob(Job):
    _input_ports = [b for b in job_properties.itervalues()]+[('machine', '(edu.ethz.sci.vistrails.batchq:Machine)'),]
    _output_ports = [('job', '(edu.ethz.sci.vistrails.batchq:Job)'),]

    def compute(self):  
        mac = self.getInputFromPort("machine")
        queue, cls = mac.queue, mac.queue_cls
        kwargs = self.get_kwargs(cls)
        self.queue =cls(queue, **kwargs) 
        self.setResult("job", self)
        
def function_compute(self):
    queue = self.getInputFromPort('queue').queue
    ret = getattr(queue, self.function_name)().val()
    if isinstace(ret, FunctionMessage) and ret.code != 0:
        raise ModuleSuspended(ret.message) if ret.code > 0 else ModuleError(ret.message)
    
    self.setResult("queue", queue)
    self.setResult("result", ret)
    self.setResult("string", str(ret))

members = [ ('_input_ports', [('job', '(edu.ethz.sci.vistrails.batchq:Job)'),] ),
            ('_output_ports', [('job', '(edu.ethz.sci.vistrails.batchq:Job)')] ),
            ('compute', function_compute )]
_modules += [Job, PrepareJob] 
for name in operations.iterkeys():
    for t in operations_types[name]:
        dct = dict(members+[('function_name',name)])
        if not t is None:
            dct['_output_ports'].append( ('result', typeconversion[t]) )
        append = "" if len(operations_types[name]) == 1 else capiltalise(str(t))
        prepend = "" 
        if t in [str,int, float]: prepend = "get"
        if t in [bool]: prepend = "is"

        _modules.append(type(prepend + "".join([capitalise(a) for a in name.split("_")]) + append, (Module,NotCacheable,),dct) )
