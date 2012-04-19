from batchq.core.process import Process
from batchq.core.utils import which

print "Starting bash found at", which("bash")
x = Process(which("bash"))

# Waits until we have the prompt
while x.getchar() != "$": pass

# Sends a command to the terminal
x.write("echo Hello world\n")

# And read the response
print ""
print "The response is:"
print x.read()
print ""
print "The full buffer is:"
print x.buffer
x.kill()
