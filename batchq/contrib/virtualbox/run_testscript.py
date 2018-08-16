## Copyright 2012 (c) Troels F. Roennow
from batchq.core.errors import CommunicationTimeout
from batchq.pipelines.shell import BashTerminal as LocalMachine
from batchq.pipelines.shell import SSHTerminal as RemoteMachine
from batchq.pipelines.shell.ssh import BaseSecureTerminalHostVerification 
from batchq.pipelines.shell import SFTPTerminal as SFTP
import logging
import copy
from colorlogging import ColorizingStreamHandler
import time
import re
import sys

class TestModule(object):

    def __init__(self, filename):
        self._logger =  logging.getLogger('Virtual Machine Test: %s'%filename) #logging
        self._logger.setLevel(logging.INFO)
        ch = ColorizingStreamHandler()
        formatter = logging.Formatter('[%(levelname)s] - %(asctime)s - %(name)s - %(message)s')
        ch.setFormatter(formatter)
        ch.setLevel(logging.INFO)
        self._logger.addHandler(ch)

        self._lmachine = LocalMachine()
        self._sshconnection = None
        self._sftpconnection = None
        self._ssh_time_wait = 3
        self._port = 3022



        ## Parsing the script
        file = open(filename)
        self._filename =filename
        script = file.read()
        file.close()
        lines = script.split("\n")
        lines = [(i, lines[i-1].strip()) for i in range(1,len(lines)+1)]
        self._lines = [y for y in filter(lambda x: x[1]!="" and ( x[1].startswith("#:") or not x[1].startswith("#")),  lines)]


        ## Defining the running environment
        def timeout(to):
            self._start_ssh_if_none()            
            self._logger.info("Setting expect timeout to %d."%int(to))
            self._sshconnection.set_timeout(int(to))

        def respond(token, answer):
            self._start_ssh_if_none()
            self._expect_token += "|"+token
            self._answers.append( (token, answer, re.compile(token)) )

        def allow_fail():
            self._start_ssh_if_none()
            self._nofail = False

        def has_vm(name):
            return self.has_vm(name)

        def clone(name):
            return self.clone(name)

        def isdir(name):
            self._start_ssh_if_none()
            return self._sshconnection.isdir(name)

        def send_command(cmd):
            self._start_ssh_if_none()
            return self._sshconnection.send_command(cmd)

        def isfile(name):
            self._start_ssh_if_none()
            return self._sshconnection.isfile(name)

        def exists(name):
            self._start_ssh_if_none()
            return self._sshconnection.exists(name)

        def runif(condition):
            self._run_next = bool(condition)

        def sendfile(f,t):
            self._start_ssh_if_none()
            self._logger.info("Transfering '%s' -> '%s'" %(f,t))
            self._sftpconnection.sendfile(f,t)

        def getfile(f,t):
            self._start_ssh_if_none()
            self._logger.info("Transfering '%s' <- '%s'" %(f,t))
            self._sftpconnection.getfile(f,t)

        def export(name, *values):
            newarr = []
            for oldconf in self._exports:
                for a in  values:
                    n = copy.deepcopy(oldconf)
                    n[name] = a
                    newarr.append(n)
            self._exports = newarr

        self._locals = {'send_command':send_command, 'export': export, 'sendfile':sendfile, 'getfile':getfile, 'runif':runif,'isdir':isdir, 'isfile':isfile, 'exists':exists, 'clone': clone, 'has_vm':has_vm, 'allow_fail':allow_fail, 'respond':respond, 'timeout': timeout, '__file__': filename}
        self._globals = {}


        self._reset()

    def _reset(self):
        self._bash_token= "#-->"
        self._expect_token=self._bash_token
        self._answers = []
        self._nofail = True
        self._run_next  = True
        self._exports = [{'dummy':'dummy'}]

    def start_virtual_machine(self):
        self._image =self._get_variable("image")
        self.network_interface()
        self.port_forwarding() 


        self._logger.info( "Booting up virtual machine.")
        cmd = "VBoxManage startvm %s #--type=headless" % self._image
        out = self._lmachine.send_command(cmd)    
        job = self._lmachine.last_exitcode()
        if job != 0: 
            self._logger.info( "Failed to start virtual machine. Machine already running?")


        user = self._get_variable("user")
        password = self._get_variable("password")

        cont = True
        self._sshconnection = None
        while cont:
            self._logger.info( "Waiting for SSH to open on port %d ..." %self._port )
            try:
                self._sshconnection = RemoteMachine("localhost", user,password, self._port, additional_arguments = "-o ConnectTimeout=2", accept_fingerprint=True, debug_level=0)
                cont = False
            except BaseSecureTerminalHostVerification as e:
                self._logger.error("SSH host verification failure:\n\n%s\n" % e.ssh_message)

                self._logger.info("Deleting line %d in %s." % (e.ssh_line, e.ssh_filename))
                f = open(e.ssh_filename, "r")
                cont = f.read().split("\n")
                f.close()


                cont = cont[0:(e.ssh_line-1)] + cont[e.ssh_line:]

                f = open(e.ssh_filename, "w")
                f.write("\n".join(cont))
                f.close()
#                raise
            except:
                time.sleep( self._ssh_time_wait )

        self._sftpconnection = SFTP("localhost", user,password, self._port,  accept_fingerprint=True, debug_level=0)

        
        self._logger.info("SSH to virtual machine successfully running.")

    def shutdown(self):
        self._logger.info("Shutting down.")
        self._image = self._get_variable("image")
        cmd = "VBoxManage acpipowerbutton %s" % self._image
        self._logger.debug(cmd + " (via send_command)")
        self._lmachine.send_command(cmd)
        job = self._lmachine.last_exitcode()
        if job != 0: 
            self._logger.error("Failed to shut down virtual machine " + image_name)

    
    def network_interface(self):
        self._logger.info( "Setting up network interface to NAT for the virtual machine.")
        cmd = "VBoxManage modifyvm %s --nic1 nat" % self._image
        self._lmachine.send_command(cmd)
        job = self._lmachine.last_exitcode()
        if job != 0: 
            self._logger.error("Failed to network interface to NAT. Maybe the machine is already running?")

    def port_forwarding(self):
        self._logger.info( "Setting port fowarding up.")
        cmd = "VBoxManage modifyvm %s --natpf1 \"ssh,tcp,,3022,,22\"" % self._image
        out = self._lmachine.send_command(cmd)
        job = self._lmachine.last_exitcode()
        if job != 0: 
            self._logger.error("Failed to setup port forwarding: \n\n%s\n" % out )

    def _start_ssh_if_none(self):
        if self._sshconnection is None:
            self.start_virtual_machine()
            if self._sshconnection is None:
                raise BaseException("No SSH connection available.")


    def delete(self, name):
#        VBoxManage unregistervm     <uuid>|<name> [--delete]
        pass

    def has_vm(self, name):
        self._logger.info( "Checking whether '%s' exists." % name)
        cmd = "VBoxManage list vms" 
        vms = [x.rsplit(" ",1)[0][1:-1] for x in  self._lmachine.send_command(cmd).split("\n")]
        return name in vms


    def _get_variable(self, name):
        if name in self._locals:
            return self._locals[name]
        if name in self._globals:
            return self._globals[name]
        raise BaseException("Variable '%s' not set." % name)        

    def _set_variable(self, name, val):
        if name in self._locals:
            self._locals[name] = val
            return
        if name in self._globals:
            self._globals[name] = val
            return

    def clone(self, new_name):
        self._image =  self._get_variable("image")

        if self.has_vm(new_name):
            self._set_variable("image", new_name)
            self._image = new_name
            self._logger.info( "Using existing clone.")
            return

        self._logger.info( "Cloning VM: %s -> %s." %(self._image, new_name))
        cmd = "VBoxManage clonevm  %s --mode machine --name \"%s\" --register" % (self._image, new_name)
        out = self._lmachine.send_command(cmd)
        job = self._lmachine.last_exitcode()
        if job != 0: 
#            print self._lmachine.buffer
            self._logger.critical("Failed to clone VM:\n\n%s\n" %out  )
            sys.exit(-1)

        self._set_variable("image", new_name)
        self._image = new_name
        return True

    def __call__(self):
        
        for n, l in self._lines:
            if l.startswith("#:"):
                exec compile("\n"*(n-1) + l[2:].strip(),self._filename,'single') in self._locals, self._globals
            else:
                self._start_ssh_if_none()
                if not self._run_next :
                    self._logger.info("Skipping $ %s (line %d)" % (l,n)) 
                    self._reset()
                    continue 

                for environ in self._exports:
                    if len(environ) > 1:
                        self._logger.info("Setting environment.")
                        for name, val in environ.items():
                            out = self._sshconnection.send_command("export %s=\"%s\""%(name, val))

                    if self._expect_token==self._bash_token:
                        self._logger.info("$ "+l+" (via send_command)")
                        out = self._sshconnection.send_command(l)
                        code = self._sshconnection.last_exitcode()

                        if code !=0 and self._nofail:
                            self._logger.critical("Non-zero exitcode not allowed. Type # allow_fail() before command to allow failure. Output reads:\n\n%s\n"%out.strip())
## TODO: enable                            break
                        if code!=0:
                            self._logger.info("Returned: "+str(code))
                    else:
                        self._logger.info("$ "+l+" (via write, expects: '%s')"%self._expect_token)
                        self._sshconnection.write(l+"\n")
                        self._sshconnection.consume_output(consume_until="\n")
                        cont = True
                        while cont:
                            if not self._sshconnection.isalive(): 
                                cont = False
                                break
                            try:
                                exp = self._sshconnection.expect(re.compile(self._expect_token))
                                if exp.endswith(self._bash_token):
                                    cont = False
                                    break
                                self._logger.info("Program asks:\n\n%s\n" % exp.split("\n")[-1])
                            except CommunicationTimeout:
                                self._logger.error("Communication timeout recieved.")
                                cont = False
                                break
                            self._logger.info("Looking for answer.")
                            cont = False
                            for tok,ans,pat in self._answers:
                                self._logger.debug("Testing: '%s'" % tok)
                                if pat.search(exp):
                                    cont = True
                                    self._logger.info("Answer: '%s'" % ans)
                                    self._sshconnection.write(ans+"\n")
                                    self._sshconnection.consume_output(consume_until="\n")
                                    break
                            if not cont:
                                self._logger.critical("No answer found.")                      

                self._reset()

        x._sshconnection.flush_pipe()
        self._logger.info("SSH session: \n\n%s\n" % self._sshconnection.buffer.replace(self._bash_token,"$ "))
        x._sftpconnection.flush_pipe()
        self._logger.info("SFTP session: \n\n%s\n" % self._sftpconnection.buffer)
        x._lmachine.flush_pipe()
        self._logger.info("Local bash session: \n\n%s\n" % self._lmachine.buffer.replace(self._bash_token,"$ "))









x = TestModule("ubuntu32")
try:
    x()
except:
    if not x._sshconnection is None:
        x._sshconnection.flush_pipe()
        print x._sshconnection.buffer

    raise
#print 
#print

