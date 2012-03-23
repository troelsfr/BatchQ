from batchq.queues import  LSFBSub
from batchq.core.batch import DescriptorQ, load_queue

q = load_queue(LSFBSub, "brutus,tronnow") 
for i in range(1,15):
    desc = DescriptorQ(q, command="./sleepy %d" %i, input_directory=".", output_directory=".", overwrite_submission_id="simu%d" %i, subdirectory="mysimulation")
    print "Handling job %d" %i
    desc.job()
