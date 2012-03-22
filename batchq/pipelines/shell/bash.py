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
from batchq.core.errors import HashException
from batchq.core.utils import which 


import posixpath
import hashlib
import os
import re
import time

def format_path(path):
    return path.replace(r" ",r"\ ").replace(r"(",r"\(").replace(r")",r"\)").replace("\"","\\\"").replace("\'","\\\'")


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

          # bash, python
HASHERS = [("md5", "md5", "(?P<hash>[a-fA-F\d]{32})"),
           ("md5sum", "md5", "(?P<hash>[a-fA-F\d]{32})"),
           # TODO: patterns below here needs to be fixed
           ("shasum", "sha1","(?P<hash>[a-fA-F\d]{32})"),   
           ("sha1sum", "sha1","(?P<hash>[a-fA-F\d]{32})"), 
           ("shasum-5.12", "sha512","(?P<hash>[a-fA-F\d]{32})"),
           ("sha512sum", "sha512","(?P<hash>[a-fA-F\d]{32})")]

class BashTerminal(BasePipe):
    """
    Unless another pipe is supplied this constructor opens bash and
    sets the path module along with the expectation token and the
    submit token. The expectation token is the prompt characters and should be
    chosen such that one would not expect it to appear in any output
    of any of the executed programs. The token is set in
    ``BashTerminal.initiate_pipe()`` which is called if ``initiate_pipe
    = True`` (default). The submit token is the token that will be send
    to the pipe after the command has been sent and the command echo has been
    consumed. For a normal bash terminal this is simply ``\\n``.
    """
    def __init__(self, pipe = None, expect_token ="#-->", submit_token = "\n", path_module = None, initiate_pipe = True):
        if not pipe:
            cmd = which("bash")
            pipe = Process(cmd, terminal_required = True)

        if not path_module:
            self._path = os.path
        else:
            self._path = path_module

        self._hasher = None
        super(BashTerminal, self).__init__(pipe,expect_token, submit_token,initiate_pipe=initiate_pipe)        
        self.set_timeout(10)
        self._nodename = None

    def initiate_pipe(self):
        """
        This function evaluates the commands that will be unique for our
        bash session. This functions changes the promt such that it will
        be the same independently of the user.
        """

        self._pipe.write("export PS1=\"%s\"" % self._expect_token)
        self.consume_output()
        self._pipe.write(self._submit_token)  
        self.consume_output()

        self.send_command("unset HISTFILE")
        self._entrance = self.send_command("pwd").strip()

    def entrance(self):
        return self._entrance

    def push_entrance(self):
        return self.pushd(self._entrance)


    @property    
    def path(self):
        """
        This function returns the path object for the system on which
        the terminal runs. This function is
        implemented as a matter of convience as different terminals may
        be based on different standards. You can for instance not rely on
        os.path when controlling SSH from a Windows machine.
        """
        return self._path

    def last_modified(self, path):
        """
        This function returns the last modification time of the given
        directory or file.
        """
        global DATETIME_FORMAT
        quotepath = "'%s'" % path
        res = self.send_command('stat -f "%Sm" -t "'+DATETIME_FORMAT+'" '+ quotepath).strip()
        return time.strptime(res, DATETIME_FORMAT)
        
    def echo(self, msg, output = None):
        """
        Echo a message to output. If output is None, then echo is undirected. 
        """
        if output is None:
            return self.send_command("echo %s" % msg)
        else:
            return self.send_command("echo %s > %s" % (msg,output))

    def cat(self, filename):
        """
        Returns the contents of a file.
        """
        return self.send_command("cat %s" % filename)


    def cp(self, source, dest, recursively = False):
        """
        Copies source to dest. If recursive is set to True directories
        are recursively copied. 
        """        
        parameters =""
        if recursively:
            parameters +="-R "

        source = format_path(source)
        dest = format_path(dest)

        if parameters == "":
            cmd = "cp %s %s" % (source, dest)
        else:
            cmd = "cp %s %s %s" % (parameters, source, dest)

        ret = self.send_command(cmd)

        return ret.strip() == ""
        

    def rm(self, path, force=False, recursively = False):
        """
        Removes the path on the file system. 
        """
        parameters =""
        if recursively:
            parameters +="-r "
        if force:
            parameters +="-f "

        path = format_path(path)
        if parameters == "":
            cmd = "rm %s" % path
        else:
            cmd = "rm %s %s" % (parameters, path)
        ret = self.send_command(cmd)

        return ret.strip() == ""
        
    def chdir(self, dir):
        """
        Changes the current working directory into dir.
        """
        cmd = "cd '%s'" % dir
        return self.send_command(cmd).strip() == ""

    def pushd(self, dir):
        """
        Changes the current working directory into dir.
        """
        cmd = "pushd '%s'" % dir
        return not "no such file or directory" in self.send_command(cmd).strip().lower()

    def popd(self):
        cmd = "popd" 
        return not "directory stack empty" in self.send_command(cmd).strip().lower()

    def home(self):
        home = self.send_command("echo $HOME").strip()
        if home == "":
            home = self.send_command("echo ~").strip()
        return home

    def mkdir(self, dir, create_intermediate = False):
        if create_intermediate:
            cmd = "mkdir -p %s" % format_path(dir)
        else:
            cmd = "mkdir %s" % format_path(dir)

        ret = self.send_command(cmd)

        return ret.strip() == ""

    def set_permission(self, file, permissions):
        cmd = "chmod %s %s"%(permissions, format_path(file) )
        ret = self.send_command(cmd)
        return ret.strip() == ""

    def dirname(self,object):
        """
        This function tries to retrieve the directory name of object and
        resolve all symlinks.
        """
        cmd = "SOURCE=\"%s\"\n" % object
        cmd +="""        
while [ -h "$SOURCE" ] ; do SOURCE="$(readlink "$SOURCE")"; done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
echo $DIR"""
        ret = self.send_command(cmd).strip()
        if ret == "":
            return None
        return ret

    def pwd(self):
        return self.send_command("pwd").strip()

    def whoami(self):
        """
        Invokes ``whoami`` in the terminal and returns the /result.
        """
        return self.send_command("whoami").strip()


    def overwrite_nodename(self,name):

        self._nodename =name


    def nodename(self):
        """
        Returns the node name.
        """
        if not self._nodename is None:
            return self._nodename
        return self.send_command("uname -n").strip()

    def system_string(self):
        """
        Returns an indetification string for the system.
        """
        return self.send_command("uname -a").strip()

    def system_info(self):
        """
        Returns hardware information for the system.
        """
        info = "No system information found"
        if self.exists("/proc/cpuinfo"):
            info = "="*20 + " CPU "+ "="*20+"\n"
            info += self.send_command("cat /proc/cpuinfo")
            info +="\n"
            info += "\n\n"+"="*20 + " MEM "+ "="*20+"\n"
            info += self.send_command("cat /proc/meminfo")
            info +="\n"
        elif self.command_exists("system_profiler"):
            info = self.send_command("system_profiler")
        return info



    def last_pid(self):
        """
        Returns the pid of the last started proccess. If this is
        not possible 0 is returned.
        """
        try:
            return int(self.send_command("echo $!").strip())
        except:
            return 0

    def last_exitcode(self):
        """
        Returns the exit code of the last started proccess. If this is
        not possible ``None`` is returned.
        """
        try:
            return int(self.send_command("echo $?").strip())
        except:
            pass
        return None

    def isrunning(self, pid):
        """
        Returns ``True`` if the ``pid`` is found in the systems process list.
        """
        try:
            self.send_command("kill -0 %d" % int(pid)).strip()
        except:
            return False
        return self.last_exitcode() == 0

    def isfile(self, filename):
        """
        Returns ``True`` if ``filename`` is a file.
        """
        cmd = "if [ -f '%s' ]; then echo \"SUCCESS\"; fi" % filename
        output1 = self.send_command(cmd).strip()
        return  output1 == "SUCCESS"

    def isdir(self, dir):
        """
        Returns ``True`` if ``dir`` is a directory.
        """
        cmd = "if [ -d '%s' ]; then echo \"SUCCESS\"; fi" % dir
        output1 = self.send_command(cmd).strip()
        return  output1 == "SUCCESS"

    
    def exists(self, path):
        """
        Returns ``True`` if ``path`` is either a directory or a file.
        """
        return self.isdir(path) or self.isfile(path)


    def command_exists(self, path):
        """
        Checks whether a commmand exists in the environment path or not. 
        """
        cmd = "command -v %s >/dev/null && echo \"SUCCESS\"" % format_path(path)
        return self.send_command(cmd).strip() == "SUCCESS"

    @property
    def hasher(self):
        """
        This property returns a tuple containing the bash command for
        doing a hash, the corresponding Python routine (as string) and a
        regex pattern that matches the hash.
        """
        global HASHERS
        if self._hasher: return self._hasher

        for p in HASHERS:
            cmd, _,_ = p
            if self.command_exists(cmd):
                self._hasher = p
#                print "Found hasher ", p
                break            
        return self._hasher

    def _extract_hash(self, pattern, response):
        searcher_for = re.compile(pattern)
        match = searcher_for.search(response)
        if not match:
            raise HashException("The output '%s' did not contain a hash string of the expected format."%response)

        return match.group("hash")


    def file_hash(self, filename, check_file = True):
        if check_file  and not self.isfile(filename):
            raise HashException("%s is not a file."%filanem)

        hasher, algorithm, pattern = self.hasher
        cmd = "%s '%s'" % (hasher, filename)
        
        response = self.send_command(cmd).strip()
        return self._extract_hash(pattern,response)

    def directory_hash(self, dir, ignore_hidden=False, silent=False):
        if not self.isdir(dir):
            path = self.pwd()
            if not silent:
                raise HashException( "Could not hash '%s' from directory '%s' because it is not a directory."%(dir, path))
            return False

        hasher, algorithm, pattern = self.hasher

        cmd = "find '%s' -type f -print0 | sort -z | xargs -0 cat | %s" % (dir, hasher)

        if ignore_hidden:        
            cmd = "find '%s' \( ! -regex '.*/\..*' \)   -type f -print0  | sort -z | xargs -0 cat | %s" % (dir, hasher)
    
        response = self.send_command(cmd).strip()
        return self._extract_hash(pattern,response)


    def hash(self, path):
        if self.isfile(path):
            return self.file_hash(path, check_file=False)
        else:
            return self.directory_hash(path)

    def list(self, dir = ".", recursively = True):
        """
        List files in directory.

        Warning! If recursively is True, all subdirectories are included
        (also hidden ones, i.e. staring with '.'). Consequently, this
        command will execute extremely slowly if many levels of
        recursion occur. 
        """
        self.send_command("pushd '%s'"% dir.replace(r" ", r"\ "))

        formatter = lambda x: x[2:len(x)].strip() if len(x) >2 and x[0:2] =="./" else x.strip()

        filt = lambda x: not x.strip() == "" and not x.strip() == "." 
        first_level = lambda x: not r"/" in x

        append = ""
        if not recursively: append = " -maxdepth 1"
        file_list = self.send_command("find . -type f%s"%append).split("\n")
        dir_list = self.send_command("find . -type d%s"%append).split("\n")

        files =filter(filt, [formatter(x) for x in file_list])
        dirs = filter(filt, [formatter(x) for x in dir_list])
        if not recursively:
            files =filter(first_level, files)
            dirs = filter(first_level, dirs)


        self.send_command("popd")

        return (files, dirs)




if __name__ == "__main__":

    x = BashTerminal()
    server = "localhost"
    files, dirs = x.list(recursively = False)
    pwd = x.pwd()

    print "On", server, "is following files "
    for file in files:
        print "     -", file
    print "and following directories"
    for d in dirs:
        print "     -", d,"."
    print "in", pwd
