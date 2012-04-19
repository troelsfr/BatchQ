from batchq.core import batch
lsharp = 40
print ""
print "#"*lsharp
print "## 00 - a : Hello world"
print "#"*lsharp
class TestPipe1(object):
    def hello_world(self):
        print "Hello world"

class Q1(batch.BatchQ):
    pipe = batch.Controller(TestPipe1)
    fnc = batch.Function().hello_world()

instance = Q1()
print ""
print "Calling fnc"
instance.fnc()

print ""
print "#"*lsharp
print "## 00 - b : Hello error"
print "#"*lsharp
class Q2a(batch.BatchQ):
    pipe = batch.Controller(TestPipe1)

    # Here we indicate that errors should be printed
    fnc1 = batch.Function(verbose=True).hello_world("Hello error")

    # Default is not to print errors
    fnc2 = batch.Function(verbose=False).hello_world("Hello error")

instance = Q2a()

try:
    instance.fnc1()
except:
    print "An error occured in fnc1"

try:
    instance.fnc2()
except:
    print "An error occured in fnc2"


print ""
print "#"*lsharp
print "## 00 - c : Hello property"
print "#"*lsharp

class TestPipe2(object):
    def hello_world(self, msg):
        print msg

class Q3(batch.BatchQ):
    message = batch.Property("Hello property")
    pipe = batch.Controller(TestPipe2)
    fnc = batch.Function().hello_world(message)

print ""
print "Creating instance without argument: "
instance = Q3()
instance.fnc()

print ""
print "Creating instance with argument: "
instance = Q3("Hello constructor argument")
instance.fnc()

print ""
print "#"*lsharp
print "## 00 - d : Hello inherit"
print "#"*lsharp


class Q4(batch.BatchQ):

    pipe = batch.Controller(TestPipe2)
    fnc1 = batch.Function(verbose=True).hello_world("Hello from FNC1")
    fnc2 = batch.Function(fnc1,verbose=True).hello_world("Hello from FNC2")

instance = Q4()
print ""
print "Calling fnc1: "
instance.fnc1()
print ""
print "Calling fnc2: "
instance.fnc2()

print ""
print "#"*lsharp
print "## 00 - e : Hello replacement"
print "#"*lsharp


class TestPipe3(object):
    def hello_world(self, msg):
       
        print msg[::-1]

class Q5(Q4):
    pipe = batch.Controller(TestPipe3)
#print "NEWFFIELDS", Q5.__new_fields__
#print "Q5", dir(Q5)
#print dir(Q5.__class__)

instance = Q5()
#print instance.fields
print ""
print "Calling fnc1: "
instance.fnc1()
print ""
print "Calling fnc2: "
instance.fnc2()


print ""
print "#"*lsharp
print "## 00 - f : Hello wildcard"
print "#"*lsharp
class TestPipe4(object):
    def fnc1(self):
        return "Function 1"

    def fnc2(self):
        return "Function 2"

    def fnc3(self):
        return "Function 3"

    def fnc4(self):
        return "Function 4"

    def fnc5(self):
        return "Function 5"

    def display(self, msg):
        print msg
        return "Display Function I"
    def display2(self, msg1, msg2):
        print "1: ", msg1
        print "2: ", msg2
        return "Display Function II"


class Q6(batch.BatchQ):
    _ = batch.WildCard()
    _r = batch.WildCard(reverse = True)
    _l = batch.WildCard(lifo = False)
    _lr = batch.WildCard(lifo = False, reverse = True)
    _3 = batch.WildCard(select = 3)

    pipe = batch.Controller(TestPipe4)

    call_fnc = batch.Function() \
        .fnc1() \
        .fnc2() \
        .fnc3() \
        .fnc4() \
        .fnc5() 

    test1 = batch.Function(call_fnc) \
        .display(_)

    test2 = batch.Function(call_fnc) \
        .display2(_,_)

    test3 = batch.Function(call_fnc) \
        .display2(_r,_r)

    test4 = batch.Function(call_fnc) \
        .display2(_l,_l)

    test5 = batch.Function(call_fnc) \
        .display2(_lr,_lr)

    test6 = batch.Function(call_fnc) \
        .display(_3)

    display1 = batch.Function().fnc1()


instance = Q6()
print ""
print "Calling test1"
instance.test1()
print ""
print "Calling test2"
instance.test2()
print ""
print "Calling test3"
instance.test3()
print ""
print "Calling test4"
instance.test4()
print ""
print "Calling test5"
instance.test5()
print ""
print "Calling test6"
instance.test6()

print "A function call returns"
print instance.display1()
print ""
print "Use Function().val() = '", instance.display1().val(), "', to get the value"


