from batchq import queues
from batchq.core.batch import BatchQ

###
# Categories
categories = {
'basic_submission': 'Basic Submission',
'job_collective_operations': "Collective operations",
'low_level': "Low-level operations"
}
##
# Helper functions
name_formatter = lambda x: x
capitalise = lambda x: x[0].upper() + x[1:].lower()
remove_underscore = lambda j, name: j.join([capitalise(a) for a in name.split("_")])

QUEUE_REGISTER = {}

type_conversion = {str:'(edu.utah.sci.vistrails.basic:String)', bool:'(edu.utah.sci.vistrails.basic:Boolean)', int:'(edu.utah.sci.vistrails.basic:Integer)', float:'(edu.utah.sci.vistrails.basic:Float)'}

batch_queue_list = [(a, getattr(queues,a)) for a in dir(queues) if isinstance(getattr(queues,a),type) and issubclass(getattr(queues,a),BatchQ) ]
