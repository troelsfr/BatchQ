import time
import hashlib

def cacheable(timeout = -1):
    def decorator(fnc):
        def newfnc(*args, **kwargs):
            
            return fnc(*args, **kwargs)
        return newfnc
    return decorator
