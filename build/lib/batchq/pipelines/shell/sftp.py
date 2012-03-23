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

from batchq.pipelines.shell.ssh import BaseSecureTerminal
from batchq.pipelines.shell.bash import format_path
class SFTPTerminal(BaseSecureTerminal):

    def __init__(self, server, username, password, port = 22, accept_figerprint = False):
        super(SFTPTerminal,self).__init__(server, username, password, port, accept_figerprint, "sftp", "-oPort=%d", "sftp>")

    def initiate_pipe(self):
        pass

    def chdir(self, path):
        res = self.send_command("cd %s" % format_path(path) )
#        print "GOT: ", res, res.strip() == ""
        return res.strip() == ""


    def local_chdir(self, path):
        res = self.send_command("lcd %s" % format_path(path))
#        print "GOT: ", res, res.strip() == ""
        return res.strip() == ""

    def pwd(self):
        res = self.send_command("pwd").split(": ",1)
        return res[1].strip()

    def local_pwd(self):
        res = self.send_command("lpwd").split(": ",1)
        return res[1].strip()


    def sendfile(self, local_file, remote_file):
        res = self.send_command("put %s %s" % (format_path(local_file), format_path(remote_file)) )
        if "No such file or directory" in res:
            return False
        return True

    def getfile(self, local_file, remote_file):
        res = self.send_command("get %s %s" % (format_path(remote_file), format_path(local_file)) )
        if "No such file or directory" in res:
            return False
        return True




