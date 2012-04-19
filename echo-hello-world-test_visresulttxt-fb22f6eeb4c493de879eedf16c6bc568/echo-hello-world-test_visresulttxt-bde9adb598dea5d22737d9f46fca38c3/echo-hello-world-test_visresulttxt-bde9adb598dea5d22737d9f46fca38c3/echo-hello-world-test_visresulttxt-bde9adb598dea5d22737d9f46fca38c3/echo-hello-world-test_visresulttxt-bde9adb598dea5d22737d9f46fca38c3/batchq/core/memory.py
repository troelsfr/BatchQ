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

import subprocess

class Memory(object):
    """
    This is a simple object which uses subprocess to get
    information about a process' memory usage and subprocesses.    
    """

    def __init__(self, scale = 1):
        self._scale = scale

    def process(self,pid):
        p = subprocess.Popen("ps -p %d -o rss | awk '{sum+=$1} END {print sum}'" % int(pid), shell=True, stdout=subprocess.PIPE   )
        lst = p.communicate()[0].split('\n')
        return int(lst[0])/self._scale

    def process(self,pid):
        p = subprocess.Popen("ps -p %d -o rss | awk '{sum+=$1} END {print sum}'" % int(pid), shell=True, stdout=subprocess.PIPE   )
        lst = p.communicate()[0].split('\n')
        return int(lst[0])/self._scale

    def child_processes(self,pid):
        p = subprocess.Popen("find_children() {  echo $1; for pid in $(ps -ef | awk \"{if ( \$3 == $1 ) { print \$2 }}\") ; do   find_children $pid; done ; } ; find_children %d"% int(pid), shell=True, stdout=subprocess.PIPE   )
        children = p.communicate()[0].split("\n")
        p = subprocess.Popen("ps -o rss -p %s | awk '{sum+=$1} END {print sum}'" % ",".join(children), shell=True, stdout=subprocess.PIPE   )
        lst = p.communicate()[0].split('\n')
        return int(lst[0])/self._scale

    def user(self,usr):
        p = subprocess.Popen("ps -u %s -o rss | awk '{sum+=$1} END {print sum}'" % usr, shell=True, stdout=subprocess.PIPE   )
        lst = p.communicate()[0].split('\n')
        return int(lst[0])/self._scale

    def total(self):
        p = subprocess.Popen("ps -A -o rss | awk '{sum+=$1} END {print sum}'" , shell=True, stdout=subprocess.PIPE   )
        lst = p.communicate()[0].split('\n')
        return int(lst[0])/self._scale

