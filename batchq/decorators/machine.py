from batchq.core.stack import select_machine, end_machine

def using(machine):
    def decorator(fnc):
        def newfnc(*args, **kwargs):
            select_machine(machine)
            ret = fnc(*args, **kwargs)
            end_machine()
            return ret
        return newfnc
    return decorator
