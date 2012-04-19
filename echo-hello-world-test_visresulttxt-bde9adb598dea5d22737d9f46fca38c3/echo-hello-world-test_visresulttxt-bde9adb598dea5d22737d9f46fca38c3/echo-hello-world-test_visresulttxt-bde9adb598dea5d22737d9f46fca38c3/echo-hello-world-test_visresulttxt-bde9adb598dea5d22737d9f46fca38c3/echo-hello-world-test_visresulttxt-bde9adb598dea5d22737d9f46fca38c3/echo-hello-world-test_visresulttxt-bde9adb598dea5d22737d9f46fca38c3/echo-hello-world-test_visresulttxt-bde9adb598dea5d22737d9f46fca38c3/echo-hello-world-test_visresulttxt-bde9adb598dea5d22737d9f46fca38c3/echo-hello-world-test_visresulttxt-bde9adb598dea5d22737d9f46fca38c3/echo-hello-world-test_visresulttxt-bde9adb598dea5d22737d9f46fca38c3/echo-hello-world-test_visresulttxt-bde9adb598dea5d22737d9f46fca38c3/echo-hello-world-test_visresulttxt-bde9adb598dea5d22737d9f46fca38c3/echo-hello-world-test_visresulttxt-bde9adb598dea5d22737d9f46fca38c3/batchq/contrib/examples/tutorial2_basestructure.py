class SubmissionModel(batch.BatchQ):
    param1 = Property("default value 1")
    param2 = Property("default value 2")
    # ...

    terminal1 = Controller(Class1, arg1, arg2, ...)
    
    t1_fnc1 = Function().a().b()
    t1_fnc2 = Function().c().d()
    # ...

    terminal2 = Controller(Class2, arg1, arg2, ...)

    t2_fnc1 = Function().e(param1).f(param2)
    t2_fnc2 = Function().g().h()
    # ...

    def userdef1(self):
        # ...
        pass

    def userdef2(self):
        # ...
        pass
