from batchq.core import batch

class Model(batch.BatchQ):
    ctrl = batch.Controller(object)
    fnc1 = batch.Function().Qthrow(exception = StandardError("Custom error class"))
    fnc2 = batch.Function().Qthrow("Standard error")

Model().fnc1()
Model().fnc2()
