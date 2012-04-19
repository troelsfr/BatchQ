from batchq.core import batch

class Pipe(object):
    def display(self, msg):
        print msg

class Inherits(batch.BatchQ):
    ctrl = batch.Controller(Pipe)
    fnc1 = batch.Function().display("Hello world")
    fnc2 = batch.Function(fnc1).display("Hello world II")

Inherits().fnc2()
