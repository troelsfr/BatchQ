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

class PythonTerminal(BasePipe):
    def __init__(self, pipe = None, expect_token =re.compile("(>>> |\.\.\. )"), submit_split="\n",submit_token = "\n", terminal_preferred =True):

        if not pipe:
            cmd = which("python")
            pipe = Process(cmd,[], terminal_required = True)


        self._submit_split = submit_split
        self._number_of_outlines = 1
        self._result_list = []
        super(PythonTerminal, self).__init__(pipe,expect_token, submit_token)        
        self.consume_output(consume_until = self._expect_token)
 


    def isalive(self):
        """
        This function returns True or False depending on wether the pipe
        is still alive, or not.
        """
        return self._pipe.isalive()

    @property
    def results(self):
        """
        This property is a list containing all results.
        """
        return self._result_list
        
    def send_command(self, command):
        """
        Sends a command to the Python command line.
        """
        list = re.split(self._submit_split, command)
        result = ""
        for cmd in list:
            result += super(PythonTerminal,self).send_command(cmd)
            self._result_list += [result,]

        n = len(self._result_list)
        if self._number_of_outlines > n:
            self._number_of_outlines = n
        
        return result
