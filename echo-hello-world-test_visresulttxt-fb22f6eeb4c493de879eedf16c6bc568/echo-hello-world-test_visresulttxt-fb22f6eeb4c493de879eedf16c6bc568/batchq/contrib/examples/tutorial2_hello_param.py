from batchq.core import batch
class Pipeline(object):

    def hello(self,who):
        print "Hello",who


class HelloParam(batch.BatchQ):
    message = batch.Property("Parameter")
    ctrl = batch.Controller(Pipeline)
    fnc = batch.Function().hello(message)

HelloParam().fnc()
ins1 = HelloParam("Second Instance")
ins2 = HelloParam()
ins2.message = "Property"
ins2.fnc()
ins1.fnc()
