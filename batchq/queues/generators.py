
class Directory(object):  
    def __init__(self, temporary = True):
        self.temporary = temporary
    def __call__(self, *args,**kwargs):
        pass
class File(object):  
    def __init__(self, ext="", temporary = True):
        self.temporary = temporary
        self.extension = ext
    def __call__(self, *args,**kwargs):
        pass
