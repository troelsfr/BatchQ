import sys
import cProfile
import pstats
from batchq.queues import  LSFBSub
from batchq.core.batch import BatchQ, load_queue, Collection, Function
print "HELLO WORLD? ?? " 
from guppy import hpy
hprof = hpy()

def generate_job_collection():
    jobs = Collection()
    q = load_queue(LSFBSub, "brutus,tronnow") 

    for i in range(0,20):
        desc = q.create_job(time=3, memory=128, diskspace= 100,mpi=True, command="./sleepy %d" %i, input_directory=".", output_directory=".", subdirectory="mysimulation%d"%i, overwrite_submission_id="simu%d" %i)     
        if i == 0: print "Generating jobs: ",
        print i,
        jobs += desc   

    return jobs

import sys 
def progressbar(n, total, cycle, cycle_size, retry , result, descriptor):
    print u"\r","["+(total-cycle_size + cycle)*"*"+(cycle_size-cycle)*" "+"]",n, "/", total, " - ", cycle,"/", cycle_size, "(",retry,")" ":", result,
    sys.stdout.flush()
 
jobs = generate_job_collection()
 

# Iterate through jobs
print
print "JOBS: ", len(jobs)
for job in jobs:
    print job.identifier()

print
# Converting a Collection object to string retrieves each job status and concatinates them
print "IDs: ", jobs.identifier()
print "Status: ", jobs.status()
print 

# You can extract some of the jobs
somejobs = jobs[0:3]
print "SLICE: ", somejobs.identifier()
print
 
import time
# Extracting submitted and non submitted jobs
print time.time()
sub = jobs.submitted()
#cProfile.run("sub = jobs.submitted()","../submittest.prof")
#p = pstats.Stats('../submittest.prof')
#p.sort_stats('cumulative').print_stats(20)
print
print "SUBMITTED:", sub
print "NOT SUBMITTED:", ~sub
print
print time.time()
# We submit the onces which was not submitted

if ~sub: 

    print "Submiting new jobs"
    s = (~sub)
    i = 0
    for a in s:
        i+=1
        print time.time()
        cProfile.run("a.run_job()","../run%d"%i)
#        print "TIME PROFILE:"
#        p = pstats.Stats('../run%d'%i)
#        p.sort_stats('cumulative').print_stats(20)
#        print
#        print "HEAP PROFILE:"
#        print hprof.heap()
#        print 
#    print

#jobs.clear_cache()
print "Status: ", jobs.status()

f = open("ssh-session.txt", "w")
f.write(jobs.objects[0].terminal.buffer)
f.close()

f = open("bash-session.txt", "w")
f.write(jobs.objects[0].local_terminal.buffer)
f.close()

f = open("sftp-session.txt", "w")
f.write(jobs.objects[0].filecommander.buffer)
f.close()
print hprof.heap()
print 
sys.exit(0) 
# wait() is by default blocking (and consequently greedy)
fin = jobs.wait().finished(progress = progressbar)
print
print "Finished: ", fin.identifier()
print "Not finished: ", (~fin).identifier()
print

# any() is non-blocking, non-greedy
submitted = jobs.any().submitted()
print "ANY:", submitted
print "ANY:", ~ submitted
print

failed = jobs.failed()
print "SUCESS (", bool(~failed), "): ", ~ failed
print "FAILED (", bool(failed), "): ", failed
print



print "Recieving reults"
# jobs.recv(progress = progressbar )
print


# Storing the output of the terminal sessions
f = open("ssh-session.txt", "w")
f.write(jobs.objects[0].terminal.buffer)
f.close()

f = open("bash-session.txt", "w")
f.write(jobs.objects[0].local_terminal.buffer)
f.close()

f = open("sftp-session.txt", "w")
f.write(jobs.objects[0].filecommander.buffer)
f.close()


# Chain  
# jobs.chain(name = None)

