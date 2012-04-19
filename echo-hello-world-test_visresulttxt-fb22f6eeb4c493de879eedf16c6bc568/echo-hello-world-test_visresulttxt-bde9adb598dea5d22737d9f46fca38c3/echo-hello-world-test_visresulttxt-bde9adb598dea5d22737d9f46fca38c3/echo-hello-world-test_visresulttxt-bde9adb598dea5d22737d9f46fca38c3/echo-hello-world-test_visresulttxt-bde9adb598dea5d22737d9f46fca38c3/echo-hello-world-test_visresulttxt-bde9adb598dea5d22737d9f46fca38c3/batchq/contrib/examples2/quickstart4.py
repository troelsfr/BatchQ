from batchq.queues import  LSFBSub
from batchq.core.batch import DescriptorQ, load_queue

q = load_queue(LSFBSub, "my_server_configuration,your_name") 
for i in range(1,10):
    desc = DescriptorQ(q, command="./sleepy %d" %i, input_directory=".", output_directory=".", overwrite_submission_id="simu%d" %i)

    print "Handling job %d" %i
    desc.job()
