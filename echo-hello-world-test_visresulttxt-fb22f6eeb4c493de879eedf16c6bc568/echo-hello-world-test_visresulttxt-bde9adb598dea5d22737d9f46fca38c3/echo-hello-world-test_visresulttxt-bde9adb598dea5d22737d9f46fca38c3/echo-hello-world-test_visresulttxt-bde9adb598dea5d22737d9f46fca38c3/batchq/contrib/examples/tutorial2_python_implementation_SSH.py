from tutorial2_python_implementation import CreateFileBash
from batchq.pipelines.shell.ssh import SSHTerminal

class CreateFileSSH(CreateFileBash):
    def __init__(self,directory, command, server, username, password):
        self.terminal = SSHTerminal(server, username, password)        
        super(CreateFileSSH,self).__init__(directory, command)

if __name__=="__main__":
    import getpass
    user = raw_input("Username:")
    pasw = getpass.getpass()
    instance = CreateFileSSH("Documents/DEMO_SSH", "echo Hello SSH > hello.txt", "localhost",user,pasw)
    instance.create_file()
