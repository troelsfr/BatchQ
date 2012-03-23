from batchq.queues import  LSFBSub
from batchq.core.batch import DescriptorQ

class ServerDescriptor(DescriptorQ):
  queue = LSFBSub
  username = "default_user"
  server="brutus.ethz.ch"
  port=22
  prior = "module load open_mpi goto2 python hdf5 cmake mkl\nexport PATH=$PATH:$HOME/opt/alps/bin"
  working_directory = "Submission"

desc1 = ServerDescriptor(username="tronnow",command="./sleepy 1", input_directory=".", output_directory=".")
desc2 = ServerDescriptor(desc1, command="./sleepy 2", input_directory=".", output_directory=".")

print "Handling job 1"
desc1.job()
print "Handling job 2"
desc2.job()
