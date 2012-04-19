from batchq.core import batch
class ErrorTest(batch.BatchQ):
    ctrl = batch.Controller(object)
    fnc1 = batch.Function(verbose=True).hello_world("Hello error")
    fnc2 = batch.Function(verbose=False).hello_world("Hello error")

instance = ErrorTest()
try:
    instance.fnc1()
except:
    print "An error occured in fnc1"
try:
    instance.fnc2()
except:
    print "An error occured in fnc2"

