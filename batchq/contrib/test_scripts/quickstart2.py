from batchq.queues import  LSFBSub
from batchq.core.batch import Collection

class ServerDescriptor(LSFBSub):
  username = "default_user"
  server="brutus2"
  port=22
  prior = "module load open_mpi goto2 python hdf5 cmake mkl\nexport PATH=$PATH:$HOME/opt/alps/bin"
  working_directory = "Submission"

  
job1 = ServerDescriptor(username="tronnow",command="./sleepy 1", input_directory=".", output_directory=".", overwrite_submission_id="simu1")
job2 = ServerDescriptor(job1, command="./sleepy 2", input_directory=".", output_directory=".", overwrite_submission_id="simu2")


#print "Configurations"
#print "Handling job 1"
#desc1.job()
#print "Handling job 2"
#desc2.job()
#print 
#print "-"*20
#print desc1.settings
#print 
#print desc2.settings
jobs = Collection([job1, job2])
 
jobs.job()
jobs.job()
