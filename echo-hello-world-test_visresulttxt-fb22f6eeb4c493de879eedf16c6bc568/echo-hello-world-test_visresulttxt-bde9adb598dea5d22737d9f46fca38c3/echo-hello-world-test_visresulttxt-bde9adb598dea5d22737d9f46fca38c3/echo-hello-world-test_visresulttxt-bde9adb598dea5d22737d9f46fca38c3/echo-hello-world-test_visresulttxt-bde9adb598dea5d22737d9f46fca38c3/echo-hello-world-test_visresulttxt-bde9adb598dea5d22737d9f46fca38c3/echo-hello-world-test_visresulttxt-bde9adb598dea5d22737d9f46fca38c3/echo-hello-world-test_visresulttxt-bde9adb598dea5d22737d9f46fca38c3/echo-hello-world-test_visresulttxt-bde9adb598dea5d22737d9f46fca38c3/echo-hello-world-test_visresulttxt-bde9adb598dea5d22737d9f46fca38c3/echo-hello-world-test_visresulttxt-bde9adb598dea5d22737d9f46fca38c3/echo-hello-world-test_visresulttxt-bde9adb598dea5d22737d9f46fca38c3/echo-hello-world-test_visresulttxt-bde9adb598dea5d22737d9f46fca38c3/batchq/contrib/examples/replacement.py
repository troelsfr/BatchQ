from batchq.core.batch import BatchQ, Function, Property, WildCard, Controller

class Pipe(object):

    def hello(self, msg):
        print msg

    def olleh(self, msg):
        print msg[::-1]



class Test(BatchQ):
    xx = "Hello"
    msg = Property("Hello world")
    terminal = Controller(Pipe)

    fnc = Function().hello(msg)


class ReplaceMsg(Test):
    msg = Property("Hello replaced message")


class ReplaceMsg2(ReplaceMsg):
    msg = Property("Hello replaced message II")



class ReplaceFnc(Test):
    fnc = Function().olleh(Test.msg)


class Pipe(object):
    def hello(self, msg):
        print msg

class Model1(BatchQ):
    ctrl = Controller(Pipe)
    fnc = Function(verbose=True).hello("Hello from FNC")

class ReplacementPipe(object):
    def hello(self, msg):       
        print msg[::-1]

class Model2(Model1):
    ctrl = Controller(ReplacementPipe)


if __name__ == "__main__":
    x = Test()
    x.fnc()

    x = ReplaceMsg()
    x.fnc()

    x = ReplaceMsg2()
    x.fnc()

    x = Test()
    x.fnc()

    x = ReplaceFnc()
    x.fnc()

    Model1().fnc()
    Model2().fnc()
