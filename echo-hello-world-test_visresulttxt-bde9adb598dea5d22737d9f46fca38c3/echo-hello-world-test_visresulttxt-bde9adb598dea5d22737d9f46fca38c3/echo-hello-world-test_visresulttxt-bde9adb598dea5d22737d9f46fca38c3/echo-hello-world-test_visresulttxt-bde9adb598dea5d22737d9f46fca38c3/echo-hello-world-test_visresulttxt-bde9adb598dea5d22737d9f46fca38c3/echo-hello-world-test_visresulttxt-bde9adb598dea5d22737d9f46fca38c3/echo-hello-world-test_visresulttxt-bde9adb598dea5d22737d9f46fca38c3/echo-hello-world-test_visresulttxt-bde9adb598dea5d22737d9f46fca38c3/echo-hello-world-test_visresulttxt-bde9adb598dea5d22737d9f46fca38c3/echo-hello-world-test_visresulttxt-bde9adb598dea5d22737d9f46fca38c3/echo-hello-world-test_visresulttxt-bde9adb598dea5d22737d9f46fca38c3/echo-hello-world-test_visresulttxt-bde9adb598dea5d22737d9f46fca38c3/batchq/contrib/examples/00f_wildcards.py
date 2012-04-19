from batchq.core import batch

class TestPipe4(object):
    fnc1 = lambda self: "Function 1"
    fnc2 = lambda self: "Function 2"
    fnc3 = lambda self: "Function 3"
    fnc4 = lambda self: "Function 4"
    fnc5 = lambda self: "Function 5"

    def display(self, msg):
        print "1: ", msg
        return "Display function I"

    def display2(self, msg1, msg2):
        print "2: ", msg1, msg2
        return "Display Function II"


class Q6(batch.BatchQ):
    _ = batch.WildCard()
    _r = batch.WildCard(reverse = True)
    _l = batch.WildCard(lifo = False)
    _lr = batch.WildCard(lifo = False, reverse = True)
    _3 = batch.WildCard(select = 3)

    pipe = batch.Controller(TestPipe4)

    call_fnc = batch.Function() \
        .fnc1().fnc2().fnc3() \
        .fnc4().fnc5() 

    test1 = batch.Function(call_fnc).display(_)
    test2 = batch.Function(call_fnc).display2(_,_)
    test3 = batch.Function(call_fnc).display2(_r,_r)
    test4 = batch.Function(call_fnc).display2(_l,_l)
    test5 = batch.Function(call_fnc).display2(_lr,_lr)
    test6 = batch.Function(call_fnc).display(_3)


instance = Q6()
instance.test1()
instance.test2()
instance.test3()
instance.test4()
instance.test5()
instance.test6()


