class CustomMetaclass(type):
    def __init__(cls, name, bases, dct):
        print "Creating class %s using CustomMetaclass" % name
        super(CustomMetaclass, cls).__init__(name, bases, dct)
 
class BaseClass(object):
    __metaclass__ = CustomMetaclass
 
class Subclass1(BaseClass):
    pass
