from batchq.core import batch
from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal

lsharp = 40
print "#"*lsharp
print "## 01 - a : Send command to create file"
print "#"*lsharp
class CreateFile1(batch.BatchQ):
    _ = batch.WildCard()

    directory = batch.Property()
    command = batch.Property()

    terminal = batch.Pipeline(BashTerminal)
    
    create_file = batch.Function() \
        .home().chdir(_) \
        .chdir(directory).send_command(command)

instance = CreateFile1("Documents", "echo hello world > hello.txt")
instance.create_file()

print ""
print "#"*lsharp
print "## 01 - b : Send command to create file"
print "#"*lsharp
class CreateFile2(batch.BatchQ):
    _ = batch.WildCard()
    directory = batch.Property()
    command = batch.Property()

    terminal = batch.Pipeline(BashTerminal)

    create_dir = batch.Function(verbose=True) \
        .home().chdir(_) \
        .exists(directory).don(1).mkdir(directory, True) \
        .chdir(directory)
    
    create_file = batch.Function(create_dir) \
        .send_command(command)

instance = CreateFile2("Documents/D3MO_Bash", "echo hello new directory > hello.txt")
instance.directory = "Documents/DEMO_Bash"
instance.command = "echo H3ll0 w0rLD > hello.txt"
instance.create_file()


print ""
print "#"*lsharp
print "## 01 - c : Send command to create file"
print "#"*lsharp
#### Using the shortcut package this code can be reduced
from batchq.shortcuts.shell import home_create_dir, send_command
class CreateFile2Short(batch.BatchQ):
    _ = batch.WildCard()
    directory = batch.Property()
    command = batch.Property()

    terminal = batch.Pipeline(BashTerminal)

    create_dir = home_create_dir(directory,_)
    create_file = send_command(command)

instance = CreateFile2("Documents/DEMO_Short", "echo hello new directory > hello.txt")
instance.command = "echo Hello short world > hello.txt"
instance.create_file()

print ""
print "#"*lsharp
print "## 01 - d : Send command to create file"
print "#"*lsharp
#### The corresponding python code is

class CreateFile2_FullPython(object):
    def __init__(self,directory, command):
        self.directory = direc
        self.command = command
        self.terminal = BashTerminal()        

    def create_dir(self):
        home = self.terminal.home()
        self.terminal.chdir(home)

        if not self.terminal.exist(self.directory):
            self.terminal.mkdir(self.directory,True)
        
        self.terminal.chdir(self.directory)
        return self

    def create_file(self):
        self.create_dir()
        self.terminal.send_command(self.commmand)
        return self

instance = CreateFile2("Documents/DEMO_Python", "echo hello new directory > hello.txt")
instance.command = "echo Hello Python world > hello.txt"
instance.create_file()


print ""
print "#"*lsharp
print "## 01 - e : Send command to create file"
print "#"*lsharp

class CreateFile3(CreateFile2):
    server = batch.Property()
    username = batch.Property()
    password = batch.Property()

    # This overwrites our previous terminal and SSH is now used
    # instead. One of neat things about this method is that no instance
    # of Bash will be opened as the terminal is just overridden. 
    # Still a new terminal is created for every instance of the object.
    terminal = batch.Pipeline(SSHTerminal, server,username,password)


import getpass
pasw = getpass.getpass()
instance = CreateFile3("Documents/DEMO_SSH", "echo Hello SSH > hello.txt", "localhost","tfr",pasw)
instance.create_file()
