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
import subprocess
import select
import pty
import threading
import warnings
from batchq.core.errors import CommunicationIOException, CommunicationOSException, CommunicationWarning

class BaseProcess(object):

    def __init__(self, command = None, args = [], environment = None, terminal_preferred = True, terminal_required = False, check_timeout = 0.05):
        self._own_terminal = False
        self._echo = True
        self._buffer = ""
        self._seeker = 0
        self._maxread = 2000
        self._canread_timeout = check_timeout
        self._canwrite_timeout = check_timeout
        self._pipe = None
        self._terminal_preferred = terminal_preferred
        self._terminal_required = terminal_required
        self._ready = False



        if not command is None:
            self.spawn(command, args,environment)

    @property
    def has_terminal(self):
        return self._own_terminal

    @property
    def buffer(self):
        """
        This property holds the buffer of the session, i.e. a log over
        all output from the terminal.
        """
        self._updateBuffer()
        return self._buffer

    def terminate(self):
        """
        Terminates the process.
        """
        self._ready = False
        if self._pipe is None:
            return
        self._pipe.terminate()

    def kill(self):
        """
        Kills the process.
        """
        self._ready = False
        if self._pipe is None:
            return
        self._pipe.kill()

    def isalive(self):
        """
        Checks whether the process is alive or not.
        """
        if not self._pipe is None:
            return self._pipe.poll() is None

        if not self._ready:
            return False

        pid = None
        status = None
        i = 0
        while pid == 0 and i<2:  # TODO: Fix this part and test it properly
            try:
                pid, status = os.waitpid(self.pid, 0)    # TODO: either os.WNOHANG or 0
            except OSError, e: # No child processes
                if e[0] == errno.ECHILD:
                    raise ExceptionPexpect ('isalive() encountered condition where "terminated" is 0, but there was no child process. Did someone else call waitpid() on our process?')
                else:
                    raise e
            i+=1

        if pid == 0:
            return True


        if not status is None and ( os.WIFEXITED (status) or os.WIFSIGNALED (status) ): 
            self._ready = False
            return False
        return True


    def spawnTTY(self, command, args = [], environment = None):   
        """
        This is a placeholder for spawning a TTY. It should be
        overridden for the different OS'.
        """
        return False

    def _thread(self,p): 
        print p.stdout.read()

    def spawn(self, command, args = [], environment = None):  
        """
        This functions spawns command with arguments args. Note that
        command must be absolute or in the current directory. Commands
        in the system PATH will fail. To include this commands use the
        which function found in utils.
        """
        self._ready = False

        # First try to create process in new tty
        if (self._terminal_preferred or self._terminal_required) and \
                self.spawnTTY(command, args, environment):  
            self._own_terminal = True
            self._ready = True
            return True

        if self._terminal_required:
            raise CommunicationOSException("A pseudo-terminal is required for the communication, but no pseudo-terminal implementation of the communication module has been made for the present OS yet.")

        warnings.warn("You are running your process outside of a terminal. Make sure that that process is unbuffered as it otherwise will not be possible to detect 'expect' tokens.", CommunicationWarning)
        p = subprocess.Popen([command,]+args, close_fds=True, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr= subprocess.STDOUT )

        self._pipe = p
        self.flush()

        self._stdin_fd = p.stdin.fileno()
        self._stdout_fd = p.stdout.fileno()
        self._ready = True

    def flush(self):
        """
        Flushes the standard input.
        """        
        if self._pipe:
            self._pipe.stdin.flush()

    def can_read(self):
        """
        Checks wether we can read from the output stream.
        """
        try:
            r,w,e = select.select([self._stdout_fd],[],[], self._canread_timeout)
        except:
#            print "This was where it went wrong"
#            return False
            self._ready = False

        return self._stdout_fd in r

    def can_write(self):
        """
        Checks wether it is possible to write to the input stream.
        """
        try:
            r,w,e = select.select([],[self._stdin_fd],[], self._canwrite_timeout)
        except:
#            print "This was where it went wrong II"
            self._ready = False
        return self._stdin_fd in w
            
    def _updateBuffer(self):
        """
        This is an internal function which is used for updating the
        buffer. The input is flushed when this functions is called.  
        """
        self.flush()
        
        app = ""
        if self.can_read():
            app = os.read(self._stdout_fd, self._maxread)
            self._buffer += app

        while len(app) == self._maxread:

            self._buffer += app
            if self.can_read():
                app = os.read(self._stdout_fd, self._maxread)
            else:
                break

    def write(self, str):
        """
        This function writes str to the pipe.
        """
        
        if not self._ready:
            raise CommunicationIOException("No proccess has been spawned yet or process dead.")
        
        if self.can_write():
            os.write(self._stdin_fd, str   )
            self.flush()           
        else:
            print "Error, could not write"

    def read(self):
        """
        Reads as many chars as possible.
        """

        if not self._ready:
            raise CommunicationIOException("No proccess has been spawned yet or process dead.")
        self.flush()
        self._updateBuffer()

        oldp = self._seeker
        self._seeker = len(self._buffer)

        return self._buffer[oldp:]

    def getchar(self):
        """
        Returns the next char
        """
        n = len(self._buffer) 
        if self._seeker>=n: self._updateBuffer()

        oldp = self._seeker
        self._seeker +=1
        if self._seeker>n:
            self._seeker = n
            return ""

        return self._buffer[oldp]

    @property
    def pid(self):
        """
        Holds the PID of the process.
        """
        if self._pipe:
            return self._pipe.pid
        return -1

class WindowsProcess(BaseProcess):
    def __init__(self, *args, **kwargs):
        super(WindowsProcess, self).__init__(*args, **kwargs)

    def spawnTTY(self, command, args = [], environment = None):        
        try:
            self._stdin, self._stdout = os.pipe()
            subprocess.Popen(" ".join([command,]+args), env = environment, startupinfo =  subprocess.CREATE_NEW_CONSOLE, stdin = self._stdin, stdout = self._stdout, stderr=self._stdout)
        except:
            return False
        return True

import resource
class LinuxProcess(BaseProcess):
    def __init__(self, *args, **kwargs):
        super(LinuxProcess, self).__init__(*args, **kwargs)

    def spawnTTY(self, command, args = [], environment = None):    
        try:
            self._pid, self._child_fd = pty.fork()
            # Returning from master thread with the file decorator
            if self._pid != 0: 
                self._stdout_fd = self._child_fd
                self._stdin_fd = self._child_fd
                return True
        except OSError, e:
            raise CommunicationOSException("Unable to fork a PTY.")


        # Child thread in new pseudo-terminal
        self._child_fd = sys.stdout.fileno()

        # Closes files inherited from parent process
        fd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        for i in range (3, fd):
            try:
                os.close (i)
            except OSError:
                pass
        
        self._stdin_fd = fd
        self._stdout_fd = fd
        # Spawning process
        if environment is None:
            os.execv(command,[command,] + args)
        else:
            os.execvpe(command,[command,] + args, environment)

    @property
    def pid(self):
        if self._pipe:
            return self._pipe.pid
        return self._pid



#############################################################
# Finally, we define which process to use depending on the OS

import platform
system = platform.system().lower()

if system == "linux" or system == "darwin":
    Process = LinuxProcess    
elif system == "windows":
    Process = WindowsProcess    
else:
    warnings.warn("The present OS may not be supported by this module. Limited functionality should be expected.", CommunicationWarning)

