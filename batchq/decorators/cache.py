import time
import hashlib

CACHE_TABLE = {}
CACHE_CLEAR = {}
CACHE_STATISTICS = {}
CACHE_ENABLED = True


def _cache_hit_request(identifier):
    pass

def _cache_hit_counter(identifier):
    pass

def disable_cache():
    global CACHE_ENABLED
    CACHE_ENABLED = False

def enable_cache():
    global CACHE_ENABLED
    CACHE_ENABLED = True

def clear_simple_call_cache(identifier, caller):
    global CACHE_CLEAR
    if not identifier in CACHE_CLEAR:
        CACHE_CLEAR[identifier] = [caller]
    if not caller in CACHE_CLEAR[identifier]:
        CACHE_CLEAR[identifier].append(caller)

#        print "Clear cache", identifier

def simple_call_cache(identifier, caller, timeout, function, force_update = False):
    global CACHE_TABLE, CACHE_CLEAR
#    print "CACHE LOOKUP: ", identifier, caller, timeout
    last_invoked, cache = None, None
    if identifier in CACHE_TABLE:
        last_invoked, cache = CACHE_TABLE[identifier]
    now = time.time()

    if identifier in CACHE_CLEAR and caller in CACHE_CLEAR[identifier]:
        force_update = True
#        print "FORCE UPDATE", CACHE_CLEAR[identifier]

    if last_invoked is None or last_invoked+timeout < now or force_update:
        last_invoked = now
        cache = function()
        CACHE_TABLE[identifier] = last_invoked, cache
        if identifier in CACHE_CLEAR:
            del CACHE_CLEAR[identifier]
#        print "Caching", identifier
#    else:
#        print "Cache hit", identifier
    return cache

class SimpleCacheable(object):
    
    def __init__(self, arg = None):
        self.timeout = 100000
        if isinstance(arg, int):
            self.timeout = arg
        self.last_invoked = None
        self.cache = None

    def __call__(self,function):
        def newfnc():
            now = time.time()
            if (self.last_invoked is None) or \
                    (self.last_invoked +self.timeout < now):
                self.last_invoked = now
                self.cache= function()
     
            return self.cache
        return newfnc 
            
def simple_cacheable(arg = None):
    if hasattr(arg, "__call__"):
        return SimpleCacheable()(arg)
    return SimpleCacheable(arg)


class SimpleClassCacheable(object):
    
    def __init__(self, arg = None):
        self.timeout = 100000
        if isinstance(arg, int):
            self.timeout = arg
        self.cache = {}

    def __call__(self,function):
        def newfnc(clsinst):
            now = time.time()
            last_invoked, cache = None, None
            if clsinst in self.cache:
                last_invoked, cache = self.cache[clsinst]
            if (last_invoked is None) or \
                    (last_invoked +self.timeout < now):
                last_invoked = now
                cache= function(clsinst)
                self.cache[clsinst] = (last_invoked, cache)

            return cache
        return newfnc 
            
def simple_class_cacheable(arg = None):
    if hasattr(arg, "__call__"):
        return SimpleClassCacheable()(arg)
    return SimpleClassCacheable(arg)


        
if __name__ == "__main__":
    @simple_cacheable
    def test():
        return 9


    for i in range(1,10):
        test()
        time.sleep(1)
