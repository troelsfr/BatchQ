"""
This is some sort of docs??
"""
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

import os
import sys
import time
import re
from batchq.core.process import Process
from batchq.core.terminal import XTermInterpreter 
from batchq.core.errors import CommunicationIOException, BasePipeException, CommunicationTimeout
from batchq.core.memory import Memory
#from profilehooks import profile

class BasePipe(object):
    def __init__(self, pipe, expect_token, submit_token, mem_scale= 1000., vt100 = None, initiate_pipe = True, debug_level = 3):
        self._last_output = ""
        self._last_input = ""

        self._pipe = pipe
        self._expect_token = expect_token
        self._submit_token = submit_token
        self._timeout = 4000
        self._consume_delay = 0.0001

        self._expect_stack = [expect_token]
        self._submit_stack = [expect_token]
        self._n_expect_stack = 1
        self._n_submit_stack = 1
        self._debug_level = debug_level
        if vt100 is None:
            self._xterminterpreter = XTermInterpreter()
        else:
            self._xterminterpreter = vt100
        self._reset_timeout_onoutput = True
        self._memory = Memory(mem_scale)
        self.last_expect_token = None
        if initiate_pipe: self.initiate_pipe()




    @property
    def last_input(self):
        return self._last_input

    @property
    def last_output(self):
        return self._last_output


    @property
    def terminal_interpreter(self):
        """ 
        This property holds an instance of a ``XTermInterpreter``.
        """
        return self._xterminterpreter


    @property
    def buffer(self):
        """
        Contains the VT100 interpreted buffer.
        """
        return self._xterminterpreter.buffer

    @property
    def pipe_buffer(self):
        """
        Contains the true pipe buffer.
        """
        return self._pipe.buffer


    def push_submit(self, submit_token):
        self._submit_token = submit_token        
        self._submit_stack += [submit_token]
        self._n_submit_stack+=1

    def push_expect(self, expect_token):
        self._expect_token = expect_token
        self._expect_stack += [expect_token]
        self._n_expect_stack+=1

    def pop_expect(self):
        self._n_expect_stack-=1
        if self._n_expect_stack<1:
            raise BasePipeException("Expectation stack is empty.")

        self._expect_stack.pop()
        self._expect_token = self._expect_stack[-1]

    def pop_submit(self):
        self._n_submit_stack-=1
        if self._n_submit_stack<1:
            raise BasePipeException("Submit stack is empty.")

        self._submit_stack.pop()
        self._submit_token = self._submit_stack[-1]

    def initiate_pipe(self):
        """ 
        This function is a virtual function which is called 
        at the end if the objects initiation. Its purpose is to initiate
        the pipe with a series of commands. 
        """
        pass


#    @profile
    def flush_pipe(self):
        b = self._pipe.read()
        while b != "":
            self._xterminterpreter.write(b)
            b = self._pipe.read()
            print "[Continuing]",b

    def consume_output(self, pipe = None, consume_until = None, wait_for_some_output = False):
        """
        This function consumes output of the pipe which is separated
        with no more than 10 ms and returns it.
        """        
        if not pipe:
            self._assert_alive()
            pipe = self._pipe
        expect_token = None
        output = ""
        echo = ""
        self._xterminterpreter.set_mark()

        if consume_until and hasattr(consume_until, "search"):
            end_time = time.time()+self._timeout
            m = consume_until.search(output)
            while pipe.isalive() and not m:
                try:

                    b = pipe.getchar()
                except CommunicationIOException, e:                    
                    pass

                if b!="":
                    self._xterminterpreter.write(b)
                    output = self._xterminterpreter.copy()
                    echo = self._xterminterpreter.copy_echo()
                    tot_len = len(output)
                    tot_echo_len = len(echo)


                    if self._reset_timeout_onoutput and (self._xterminterpreter.monitor_echo !=""):
                        end_time = time.time()+self._timeout 

                    if self._debug_level == 2:
                        m = self._xterminterpreter.monitor
                        sys.stdout.write(m)

                if end_time<time.time():
                    if self._debug_level >= 3:
                        print "Debug level",self._debug_level
                        print "Timeout: ", self._timeout
                        print "-"*20, "BUFFER", "-"*20
                        print self._xterminterpreter.buffer[-1000:]
                        print "-"*20, "END OF BUFFER", "-"*20
                        print "-"*20, "READABLE ECHO", "-"*20
                        print self._xterminterpreter.readable_echo[-1000:]
                        print "-"*20, "END OF READABLE ECHO", "-"*20
                        print "Expecting: ", consume_until
                        print "Consumed: ", output
                        print "Escape mode:", self._xterminterpreter.escape_mode
                        if self._xterminterpreter.escape_mode:
                            print "Last escape:", self._xterminterpreter.last_escape
                    raise CommunicationTimeout("Consuming output timed out (%d > %d, dt = %d, %s). You can increase the timeout by using set_timeout(t)." %(end_time,time.time(),self._timeout, self.__class__.__name__))

                m = consume_until.search(output)
            if m:
                expect_token = m.group(0)
        elif consume_until:

            n = len(consume_until)
            tot_len = 0
            tot_echo_len = 0
            end_time = time.time()+self._timeout

            while pipe.isalive() and (tot_len < n or not consume_until == output[tot_len -n: tot_len]) and \
                    (tot_echo_len < n or not consume_until == echo[tot_echo_len -n: tot_echo_len]):

                try:
                    b = pipe.read_nonblocking_until(consume_until, True)
                except CommunicationIOException, e:
                    pass
                if b!="":
#                    print b,
                    self._xterminterpreter.write(b)
                    output = self._xterminterpreter.copy()
                    echo = self._xterminterpreter.copy_echo()
                    tot_len = len(output)
                    tot_echo_len = len(echo)
                

                    if self._reset_timeout_onoutput and (self._xterminterpreter.monitor_echo !=""):
                        end_time = time.time()+self._timeout 

                    if self._debug_level == 2:
                        m = self._xterminterpreter.monitor
                        sys.stdout.write(m)

                if end_time<time.time():
                    if self._debug_level >= 3:
                        print "Debug level",self._debug_level
                        print "-"*20, "BUFFER", "-"*20
                        print self._xterminterpreter.buffer[-1000:]
                        print "-"*20, "END OF BUFFER", "-"*20
                        print "-"*20, "READABLE ECHO", "-"*20
                        print self._xterminterpreter.readable_echo[-1000:]
                        print "-"*20, "END OF READABLE ECHO", "-"*20

                        print "Expecting: ", consume_until
                        print "Consumed: ", output
                        print "Escape mode:", self._xterminterpreter.escape_mode
                        if self._xterminterpreter.escape_mode:
                            print "Last escape:", self._xterminterpreter.last_escape
                    raise CommunicationTimeout("Consuming output timed out (%d > %d, dt = %d, %s). You can increase the timeout by using set_timeout(t)." %(end_time,time.time(),self._timeout, self.__class__.__name__))
            

            if consume_until == output[tot_len -n: tot_len]:
                output = output[0:tot_len -n]
                expect_token = consume_until
            # TODO: figure out what to do when the match is in the echo

        else:
            end_time = time.time() + self._consume_delay
            echo = ""
            while time.time()<end_time or (echo == "" and wait_for_some_output):
                b = pipe.read()
                while b !="" and pipe.isalive():                
                    self._xterminterpreter.write(b)
                    output = self._xterminterpreter.copy()
                    echo = self._xterminterpreter.copy_echo()
                    b = pipe.read()


            if self._debug_level == 2:
                sys.stdout.write(self._xterminterpreter.monitor)
            expect_token = ""

        if self._debug_level == 1:
            sys.stdout.write(output)
        elif self._debug_level == 2:
            sys.stdout.write(self._xterminterpreter.monitor)
        
        self._xterminterpreter.move_monitor_cursors()
        self.last_expect_token = expect_token
        return output

    def isalive(self):
        return self._pipe.isalive()

    def write(self, cmd):
        self._pipe.write(cmd)

    def send_command(self, cmd, wait_for_input_response = True, consume_until = None):
        """
        This function sends a command to the pipe, wait for the prompt
        to appear and return the output.
        """
        self._last_input = cmd

        self._assert_alive()
        self._pipe.write(cmd)
#        print "$$ >",cmd


        if cmd !="":
            xx= self.consume_output(wait_for_some_output = wait_for_input_response)
#            print xx,

        self._assert_alive()
        self._pipe.write(self._submit_token)

        # Next we consume the result of sending a submit token
        # This is done as bash sometimes send additional escape codes 
        # to manipulate the echo.
        self.consume_output(consume_until = consume_until if consume_until else self._submit_token)



        # Then we wait for the output        
        ret = self.consume_output(consume_until = self._expect_token)
        self._last_output = ret
#        print ret,
#        print self._xterminterpreter.readable_echo

        if False and  not cmd[0:2] == "ak" and self.__class__.__name__ == "SSHTerminal":
            print "COMMAND:: ", cmd
            print "EXPECT::  ", self._expect_token
            print "RETURN::  ", ret
            print "="*40, self.__class__.__name__, "="*40
            print self._xterminterpreter.readable_echo
            print "="*38, "END",self.__class__.__name__, "="*38
            if not hasattr(self, "i"):
                self.i = 0
            else:
                self.i+=1

        return ret


    def _assert_alive(self):
        if not self.isalive():
            raise CommunicationIOException("Pipe is no longer alive. If you are using a network connection you might try to reconnect.")

    def expect(self, val = None):
        self._assert_alive()
        if val is None:
            return self.consume_output(consume_until = self._expect_token)
        return self.consume_output(consume_until = val)

    def set_timeout(self, t):
        self._timeout = int(t)

    def remaining(self):
        self._xterminterpreter.move_monitor_cursors()
        r = self._pipe.read()

        self._xterminterpreter.write(r)

        return self._xterminterpreter.monitor

    def kill(self):
        return self._pipe.kill()

    def terminate(self):
        return self._pipe.terminate()

    def cpu_usage(self):
        # TODO: Yet to be implemented
        pass
    
    @property
    def pid(self):
        return self._pipe.pid

    @property
    def pipe(self):
        return self._pipe

    
    @property
    def memory_usage(self):
        return self._memory.process(self._pipe.pid)

    @property
    def child_memory_usage(self):
        return self._memory.child_processes(self._pipe.pid)


    @property
    def total_memory_usage(self):
        return self._memory.total()

