####################################################################################
# Copyright (C) 2011-2012
# Troels F. Roennow, ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
####################################################################################

from batchq.core.communication import BasePipe
from batchq.core.process import Process
from batchq.core.utils import which
import re

class MaplePipeline(BasePipe):
    def __init__(self, pipe = None, expect_token ="#-->", submit_split=";[ \r\n]*",submit_token = ";\n", terminal_preferred =True):
        """
        Unless another pipe is supplied this constructor opens Maple.

        The expectation token is the prompt characters and should be
        chosen such that one would not expect it to appear in any output
        of any of the executed programs. The token is set in
        MaplePipeline.initiate_pipe(). 

        The submit token is the token that will be send to the pipe
        after the command has been sent and the echo has been
        consumed. For a normal bash terminal this is simply \n.

        Remark! For now the Maple pipeline only runs through a terminal
        as the stdout buffer is not flushed often enough meaning that
        expectation tokens will not be seen and a deadlock is
        encountered. Hopefully a workaround for this will be found.
        """
        if not pipe:
            cmd = which("maple",["/Library/Frameworks/Maple.framework/Versions/17/bin/"])
            pipe = Process(cmd,["-t"], terminal_required = True)
#            pipe = Process(cmd,["-t"], terminal_preferred = terminal_preferred)


        self._submit_split = submit_split
        self._number_of_outlines = 1
        self._result_list = []
        super(MaplePipeline, self).__init__(pipe,expect_token, submit_token)        
        self.consume_output(consume_until = self._expect_token)
#        self.send_command("restart;\n");
 


    def isalive(self):
        """
        This function returns True or False depending on wether the pipe
        is still alive, or not.
        """
        return self._pipe.isalive()

    def restart_kernel(self, reset_vt100 = False):
        """
        This function tries to quit Maple using 'quit', then kills it
        and starts a new kernel.

        Note the resultlist is not cleared.
        """
        try:
            self.send_command("quit;")
            self.kill()
            self.remaining()
        finally:
#            self.__init__()
            cmd = which("maple",["/Library/Frameworks/Maple.framework/Versions/Current/bin/"])
            pipe = Process(cmd,["-t"], terminal_required = True)
            vt100 = self.vt100interpreter
            if reset_vt100:
                vt100 = None
            super(MaplePipeline, self).__init__(pipe,self._expect_token,self._submit_token, vt100 = vt100)        
            self.consume_output(consume_until = self._expect_token)

    @property
    def results(self):
        """
        This property is a list containing all results.
        """
        return self._result_list
        
    def send_command(self, command):
        """
        Sends a command to the Maple command line.
        """
        list = re.split(self._submit_split, command)
        for cmd in list:
            if not cmd == "":
                result = super(MaplePipeline,self).send_command(cmd.strip(), consume_until = ';')
                if not result.strip() == "":
                    self._result_list += [result,]

        n = len(self._result_list)
        if self._number_of_outlines > n:
            self._number_of_outlines = n
        
        ret = ""
        if self._number_of_outlines>0:            
            ret = self._submit_token.join(self._result_list[(n-self._number_of_outlines):n])
        self._number_of_outlines = 1
        return ret

if __name__ == "__main__":
    x = MaplePipeline()
    print "TESTING"
    x.send_command("restart;")
    a = x.send_command("y := x*x;")
    b = x.send_command("diff(y,x,x);")
    c = x.send_command("x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x;")
    print "RESTARTING KERNEL"
    x.restart_kernel();
    x.send_command("restart;")
    a = x.send_command("y := x*x;")
    b = x.send_command("diff(y,x,x);")
    c = x.send_command("x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x;")
    print "="*30, "WITH TERMINAL", "="*30
    print "Direct pipe buffer (with ESC codes):"
    print
    print x.pipe_buffer
    print
    print "VT100 Interpreted"
    print
    print x.buffer  
    print "="*100
    print "Is alive?", x.isalive()
    print "GOT FOLLOWING RESULTS"
    print "a =", a
    print "b =", b
    print "c =", c
    print "Overall results:"
    print x.results
    print "-"*100
    print "Is alive?", x.isalive()
    print "PID: ", x.pid
    print "Process usage: ", x.child_memory_usage
    print "Total (system) usage: ", x.total_memory_usage
# TODO: This provokes a bug    x.send_command("quit();")
    import time

#    time.sleep(20)
    x.send_command("quit;")
    print "Is alive?", x.isalive()
    x.kill()
    print "Is alive?", x.isalive()
    print x.remaining()
    
#    x = MaplePipeline(terminal_preferred= False)
#    x.send_command("restart;")
#    x.send_command("y := x*x;")
#    x.send_command("diff(y,x,x);")
#    x.send_command("x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x*x;")
#    print "="*30, "NO TERMINAL", "="*30
#    print "Direct pipe buffer (with ESC codes):"
#    print
#    print x.pipe_buffer
#    print
#    print "VT100 Interpreted"
#    print
#    print x.buffer  
#    print "="*100
#    x.kill()


