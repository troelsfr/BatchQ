from batchq.core import batch
class Pipeline(object):

    def hello_world(self):
        print "Hello world"

    def hello_batchq(self):
        print "Hello BatchQ"

class HelloWorld(batch.BatchQ):
    ctrl = batch.Controller(Pipeline)
    fnc = batch.Function().hello_world().hello_batchq()

instance = HelloWorld()
instance.fnc()
