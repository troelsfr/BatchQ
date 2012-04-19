from batchq.pipelines.shell.bash import BashTerminal

class CreateFileBash(object):
    def __init__(self,directory, command):
        self.directory = directory
        self.command = command
        self.terminal = BashTerminal()        

    def create_dir(self):
        home = self.terminal.home()
        self.terminal.chdir(home)

        if not self.terminal.exists(self.directory):
            self.terminal.mkdir(self.directory,True)
        
        self.terminal.chdir(self.directory)
        return self

    def create_file(self):
        self.create_dir()
        self.terminal.send_command(self.command)
        return self

if __name__=="__main__":
    instance = CreateFileBash("Documents/DEMO_Bash", "echo hello new directory > hello.txt")
    instance.command = "echo Hello Python world > hello.txt"
    instance.create_file()
