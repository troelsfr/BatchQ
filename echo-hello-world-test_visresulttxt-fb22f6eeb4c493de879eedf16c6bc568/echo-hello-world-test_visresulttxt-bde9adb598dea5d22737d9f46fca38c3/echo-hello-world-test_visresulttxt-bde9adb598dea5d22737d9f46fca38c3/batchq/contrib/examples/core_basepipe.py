from batchq.core.process import Process
from batchq.core.communication import BasePipe
from batchq.core.utils import which

class BashTerminal(BasePipe):
    def __init__(self):
        pipe = Process(which("bash"), terminal_required = True)
        expect_token ="#-->"
        submit_token ="\n"
        initiate_pipe=True
        super(BashTerminal, self).__init__(pipe, expect_token, submit_token, initiate_pipe)        


    def initiate_pipe(self):
        self.pipe.write("export PS1=\"%s\"" % self._expect_token)
        self.consume_output()
        self.pipe.write(self._submit_token)  
        self.consume_output()
    
    def echo(self, msg):
        return self.send_command("echo %s"%msg)

x = BashTerminal()
print "Response: "
print x.echo("Hello world")
print ""
print "VT100 Buffer:"
print x.buffer
print ""
print "Pipe Buffer:"
print x.pipe_buffer
