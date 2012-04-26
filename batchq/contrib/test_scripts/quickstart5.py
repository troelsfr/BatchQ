from batchq.queues import  LSFBSub
from batchq.core.batch import Descriptor, load_queue

def test():
    q = load_queue(LSFBSub, "brutus,tronnow") 
    for i in range(1,100):
        # 
        # 
        desc = Descriptor(q, time=3, memory=128, diskspace= 100,mpi=True, command="./sleepy %d" %i, input_directory=".", output_directory=".", subdirectory="mysimulation", overwrite_submission_id="simu%d" %i)
        print "Handling job %d" %i
        desc.job()  
    #    print  desc.status()


import cProfile
cProfile.run("test()", "../profile")
import pstats
p = pstats.Stats('../profile')
p.strip_dirs().sort_stats("cumulative").print_stats(10)

