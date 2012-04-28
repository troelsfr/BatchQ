from core.modules.vistrails_module import Module
from batchq.core.batch import Property
from common_definitions import QUEUE_REGISTER

####
# Machine definition
class Machine(Module):
    def get_kwargs(self, cls):
        
        ret = dict([(a[0],self.getInputFromPort(a[0])) for a in self._input_ports if self.hasInputFromPort(a[0]) and hasattr(cls,a[0]) and isinstance(getattr(cls,a[0]),Property)])
        ret.update({'q_interact': False})
        return ret

    def compute(self):
        global QUEUE_REGISTER
        kwargs = self.get_kwargs(self.queue_cls)
        inherits = self.getInputFromPort('inherits').queue if self.hasInputFromPort('inherits') else None

        qid = self.__class__.__name__
        print "Queue id is", qid
        if not inherits is None and qid in QUEUE_REGISTER:
            print "Inheriting already existing queue ", qid
            inherits = QUEUE_REGISTER[qid]
    
        if self.queue is None:
            self.queue = self.queue_cls(**kwargs) if inherits is None else self.queue_cls(inherits, **kwargs) 
        else:
            print "Reusing own queue "
        ## TODO: update properties of machine
            pass

        if not qid in QUEUE_REGISTER:
            print "Copying queue to ", qid
            QUEUE_REGISTER[qid] =  self.queue.create_job(q_empty_copy = True)

        print "OBJECT ID:", id(self.queue)
        self.setResult("machine", self)

module_definitions = [(Machine,{'abstract':True})]
