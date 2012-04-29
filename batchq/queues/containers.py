from os import path
from batchq.core import batch

class ContainerType(object):
    def __init__(self):
        self.field = None

    @property
    def type(self):
        return self.__class__

    def register_field(self, field):
        self.field = field

    def as_str(self, *args, **kwargs):
        raise BaseException("Virtual member 'as_str' no overwritten in class '%s'" % self.__class__.__name__)

class PathName(ContainerType):  
    def __init__(self, relative_to= "", temporary = True):
        super(PathName, self).__init__()
        self.temporary = temporary
        self.relative_to = relative_to

    def __call__(self, *args,**kwargs):        
        pass

    def as_str(self):
        rel = self.relative_to
        if isinstance(self.relative_to,batch.Property):
            rel = self.relative_to.get()
        elif isinstance(self.relative_to,batch.Function):
            rel = self.relative_to().val()
        rel = str(rel)

        ret = ""
        if isinstance(self.field, batch.Property):
            ret = self.field.get()
        elif isinstance(self.field,batch.Function):
            ## Notice, it is on purpose the field function 
            ## is not called. At this point it should have 
            ## been executed by the user
            ret = self.field.val()
        else:
            raise BaseException("Unkonwn field type '%s'." % self.field)
        ret = str(ret)
        if ret == "": return None
        if rel:
            return path.join(rel,ret)
        else:
            return ret
        
class DirectoryName(PathName):
    pass

class FileName(PathName):  
    def __init__(self, ext="", *args, **kwargs):
        super(FileName, self).__init__(*args, **kwargs)
        self.extension = ext

class TextFile(ContainerType):  
    def __init__(self, ext = "", relative_to= "", temporary = True):
        super(TextFile, self).__init__()
        self.temporary = temporary
        self.relative_to = relative_to
        self.extension = ext

    def as_str(self):
        ret = ""
        if isinstance(self.field, batch.Property):
            ret = self.field.get()
        elif isinstance(self.field,batch.Function):
            ret = self.field.val()
        else:
            raise BaseException("Unkonwn field type '%s'." % self.field)
        return ret
    
