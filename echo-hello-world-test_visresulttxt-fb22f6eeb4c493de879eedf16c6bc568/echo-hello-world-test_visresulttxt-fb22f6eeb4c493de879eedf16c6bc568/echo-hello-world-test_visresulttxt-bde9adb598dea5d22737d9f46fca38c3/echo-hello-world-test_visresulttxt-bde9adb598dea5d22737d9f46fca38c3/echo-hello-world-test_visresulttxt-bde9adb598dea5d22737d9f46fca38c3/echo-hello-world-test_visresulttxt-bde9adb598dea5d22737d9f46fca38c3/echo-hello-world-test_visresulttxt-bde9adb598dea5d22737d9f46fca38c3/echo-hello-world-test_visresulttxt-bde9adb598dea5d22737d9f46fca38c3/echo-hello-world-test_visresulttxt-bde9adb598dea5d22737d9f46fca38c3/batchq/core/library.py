
class ModuleRegister(object):   
    def __init__(self):
        self._register = {}

    def register(self, name, module):
        self._register[name] = module

    @property
    def dict(self):
        return self._register

import pkgutil
import sys
import StringIO
class Library:
    functions = ModuleRegister()
    templates = ModuleRegister()
    pipelines = ModuleRegister()
    queues = ModuleRegister()

    @staticmethod
    def find_modules():
        sys.stdout = StringIO.StringIO()
        sys.stderr = sys.stdout
        objs = pkgutil.walk_packages()
        try:
            pass
#            for a in objs:
#                a
        except:
            pass
        sys.stdout = sys.__stdout__  
        sys.stderr = sys.__stderr__  

Library.find_modules()
