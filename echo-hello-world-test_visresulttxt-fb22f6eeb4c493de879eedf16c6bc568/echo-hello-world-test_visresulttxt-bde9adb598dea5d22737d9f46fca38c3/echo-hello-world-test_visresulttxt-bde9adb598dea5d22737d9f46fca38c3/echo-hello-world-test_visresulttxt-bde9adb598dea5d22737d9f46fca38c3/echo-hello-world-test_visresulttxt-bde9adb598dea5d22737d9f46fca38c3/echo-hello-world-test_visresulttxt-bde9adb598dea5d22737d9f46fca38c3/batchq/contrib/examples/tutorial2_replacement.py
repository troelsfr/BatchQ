from batchq.core import batch

class Pipe(object):
    def hello(self, msg):
        print msg

class Model1(batch.BatchQ):
    ctrl = batch.Controller(Pipe)
    fnc = batch.Function(verbose=True).hello("Hello from FNC")

class ReplacementPipe(object):
    def hello(self, msg):       
        print msg[::-1]

class Model2(Model1):
    ctrl = batch.Controller(ReplacementPipe)

Model1().fnc()
Model2().fnc()
