from common_definitions import categories, capitalise, QUEUE_REGISTER, type_conversion, batch_queue_list, remove_underscore, name_formatter
from core.modules.vistrails_module import Module, ModuleError, NotCacheable, InvalidOutput, ModuleSuspended
from batchq.core.batch import BatchQ, Function, Property, FunctionMessage,  Collection, Exportable

import copy

from machine import module_definitions, Machine
_modules = module_definitions

####
## Creating queues/"machines"
job_properties = {}
operations = {}
operations_types = {}
operations_highlevel = {}
for name, queue in batch_queue_list:
    ## Generating queue classes
    properties = []
    for a in dir(queue):
        if isinstance(getattr(queue,a), Property):
            attr = getattr(queue,a)
            if attr.verbose and attr.invariant:
                properties.append( (a,type_conversion[attr.type])  )
            if not attr.password and not attr.invariant:
                job_properties[a] = (a,type_conversion[attr.type],not attr.verbose)
    members = { '_input_ports' : properties + [('inherits','(org.comp-phys.batchq:Machine)',True)], 'queue_cls': queue,
                '_output_ports': [('machine', '(org.comp-phys.batchq:Machine)')],
                'queue':None}

    if hasattr(queue, "__descriptive_name__"):
        descriptive_name =  queue.__descriptive_name__
    else:
        descriptive_name = name[0].upper()+name[1:].lower()

    cls = type(name_formatter(descriptive_name), (Machine,), members)

    ## Extracing all functions from the queues
    functions = [(a,getattr(queue,a)) for a in dir(queue) if isinstance(getattr(queue,a), Function) and not a.startswith("_") and getattr(queue,a).enduser]
    for f, fnc in functions:
        t = fnc.type
        if not f in operations:
            operations[f] = []
            operations_types[f] = []
            operations_highlevel[f] = False

        operations[f].append(name)
        operations_highlevel[f] = operations_highlevel[f] or fnc.highlevel

        if not t in operations_types[f]: operations_types[f].append(t)

    _modules.append((cls,{'namespace':categories['basic_submission']}))

######
## Basic Job definitions
class Job(Machine):
    pass
_modules.append((Job, {'abstract':True}))


def compute_jobpreparation(self):  
    mac = self.getInputFromPort("machine")
    queue, cls = mac.queue, mac.queue_cls
    kwargs = self.get_kwargs(cls)
    self.queue =cls(queue, **kwargs) 
    self.setResult("job", self)

dct = {'_input_ports': [b for b in job_properties.itervalues()]+[('machine', '(org.comp-phys.batchq:Machine)'),],
       '_output_ports': [('job', '(org.comp-phys.batchq:Job)'),],
       'compute': compute_jobpreparation}

PrepareJob = type(name_formatter("Prepare Job"), (Job,), dct)

_modules += [(PrepareJob, {'namespace':categories['basic_submission']})] 

#####
## Creating functions 
class JobOperation(Module,NotCacheable):
    pass

def joboperation_compute(self):
    job = self.getInputFromPort('job')
    queue = job.queue
    print "Run job was also called .... " 
    ret = getattr(queue, self.function_name)().val()
    if isinstance(ret, FunctionMessage) and ret.code != 0:
        raise ModuleSuspended(self, ret.message) if ret.code > 0 else ModuleError(self,ret.message)
    
    self.setResult("job", job)
    self.setResult("result", ret)
    self.setResult("string", str(ret))

_modules+=[(JobOperation,{'abstract':True})]


members = [ ('_input_ports', [('job', '(org.comp-phys.batchq:Job)'),] ),
            ('_output_ports', [('job', '(org.comp-phys.batchq:Job)')] ),
            ('compute', joboperation_compute)]

low_level_functions = {}
high_level_functions = {}
high_level_modules = []
for name in operations.iterkeys():
    for t in operations_types[name]:
        dct = dict(copy.deepcopy(members)+[('function_name',name)])
        if not t is None and not t in [FunctionMessage]:
            dct['_output_ports'].append( ('result', type_conversion[t]) )

        #  TODO: Multiple types yet to be implemented
        ## append = "" if len(operations_types[name]) == 1 else capiltalise(str(t))
        namespace = categories['low_level']

        descriptive_name = remove_underscore(" ",name)
        if t in [str,int, float]: 
            low_level_functions[name] = (name,type_conversion[t])
            descriptive_name = "Get" + remove_underscore("",name)
        if t in [bool]: 
            low_level_functions[name] = (name,type_conversion[t])
            descriptive_name = "Is" + remove_underscore("",name)
        

        if not operations_highlevel[name]:
            _modules.append((type(name_formatter(descriptive_name), (JobOperation,),dct), {'namespace': namespace} ))
        else:
            namespace = categories['basic_submission']
            high_level_functions[name] = (name,type_conversion[t]) if t in type_conversion else (name,None)
            high_level_modules.append((descriptive_name, dct, namespace))
#        namespace = categories['basic_submission']


def jobinfo_compute(self):

    job = self.getInputFromPort("job")
    queue = job.queue
    print "Was called"

    self.setResult("job", job)
    ## TODO: fix me, set outputs

dct = {'_input_ports': [('job', '(org.comp-phys.batchq:Job)'),],
       '_output_ports': [b for b in job_properties.itervalues()] + [b for b in low_level_functions.itervalues()],
       'compute': jobinfo_compute}
JobInfo = type(name_formatter("Job Info"), (Job,), dct)

_modules += [(JobInfo, {'namespace':categories['basic_submission']})] 

####
# High-level function
def highlevel_compute(self):
    joboperation_compute(self)
    jobinfo_compute(self)

for descriptive_name, dct, namespace in high_level_modules:
    dct['compute'] = highlevel_compute
    _modules.append((type(name_formatter(descriptive_name), (JobInfo,),dct), {'namespace': namespace} ))

######
## Creating collective operations
class CollectiveOperation(Module,NotCacheable):
    pass
_modules.append((CollectiveOperation, {'abstract':True}))

def collective_compute(self):
    job = self.getInputFromPort('job')
    operation = self.getInputFromPort('operation')
    col = Collection() + job
    col2 = getattr(col, collection_name)()
    rets = getattr(col2, operation.function_name)().as_list()
    self.setResult('job', rets[0])

collective = dict([(name,getattr(Collection, name)) for name in dir(Collection) if isinstance(getattr(Collection, name),Exportable)])
members = [ ('_input_ports', [('operation', '(org.comp-phys.batchq:JobOperation)'),('job', '(org.comp-phys.batchq:Job)')] ),
            ('_output_ports', [('job', '(org.comp-phys.batchq:Job)')] ),
            ('compute', collective_compute ),
            ('collection_name', name)]
namespace = categories['job_collective_operations']
for name, func in collective.iteritems():
    dct = dict(members)
    _modules.append((type( "".join([capitalise(a) for a in name.split("_")]) , (CollectiveOperation,),dct),{'namespace':namespace} ))




_modules = _modules
