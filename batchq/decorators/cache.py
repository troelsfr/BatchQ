import time
import hashlib

CACHE_TABLE = {}

def cacheable(element):
    timeout = 10000000
    if isinstance(element, int) timeout = element
    def decorator(fnc):
        def newfnc(*args, **kwargs):
            
            return fnc(*args, **kwargs)
        return newfnc
    return decorator
