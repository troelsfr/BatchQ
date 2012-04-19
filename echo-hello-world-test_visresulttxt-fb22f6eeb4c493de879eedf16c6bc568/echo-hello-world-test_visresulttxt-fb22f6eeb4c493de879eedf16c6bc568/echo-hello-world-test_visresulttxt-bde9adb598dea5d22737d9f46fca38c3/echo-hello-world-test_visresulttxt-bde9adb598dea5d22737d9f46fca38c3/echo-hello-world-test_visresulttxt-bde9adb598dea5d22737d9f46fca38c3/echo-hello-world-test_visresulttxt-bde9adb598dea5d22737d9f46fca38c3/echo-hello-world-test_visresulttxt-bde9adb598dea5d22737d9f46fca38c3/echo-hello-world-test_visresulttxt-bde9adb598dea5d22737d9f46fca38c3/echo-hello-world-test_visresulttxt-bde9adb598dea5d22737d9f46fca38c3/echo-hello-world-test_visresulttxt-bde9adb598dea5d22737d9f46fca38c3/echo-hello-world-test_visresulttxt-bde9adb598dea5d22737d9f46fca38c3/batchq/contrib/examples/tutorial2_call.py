from batchq.core import batch

class Pipe(object):
    def display(self, msg):
        print msg
        return msg

class CallIt1(batch.BatchQ):
    ctrl = batch.Controller(Pipe)
    fnc1 = batch.Function().display("Hello world")
    fnc2 = batch.Function().display("Before call").Qcall(fnc1).display("After call") \
        .Qprint_stack()

CallIt1().fnc2()
print ""

class CallIt2(batch.BatchQ):
    _ = batch.WildCard()
    ctrl = batch.Controller(Pipe)
    fnc1 = batch.Function().display("Hello world")
    fnc2 = batch.Function().Qjoin(fnc1, " II").display(_)

CallIt2().fnc2()
