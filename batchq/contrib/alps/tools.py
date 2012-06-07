try:
    from pyalps.tools import executeCommand
except:
    raise BaseException("You need ALPS to import this package.")    

import os
try:
    from batchq.queues import LocalShell
    from batchq.core.batch import load_queue, BatchQ, Collection
    from batchq.core.utils import hash_filelist
    __batchq_available = True
except:
    __batchq_available = False

import copy
import simplejson as json
#from batchq.core.batch import DescriptorQ

__runapplication_std_options = {'working_directory':'.','input_directory':None,'output_directory':None, 'start_in_home': False}
__runapplication_std_queue = None

def runApplicationBackground(appname, parmfile, Tmin=None, Tmax=None, writexml=False, MPI=None, mpirun='mpirun', queue=None,  force_resubmit = False, background=True):
    """ run an ALPS application 
    
        This function runs an ALPS application. The parameers are:
        
        appname: the name of the application
        parmfile: the name of the main XML input file
        write_xml: optional parameter, to be set to True if all results should be written to the XML files in addition to the HDF5 files
        Tmin: optional parameter specifying the minimum time between checks whether a MC simulatio is finished
        Tmax: optional parameter specifying the maximum time between checks whether a MC simulatio is finished
        MPI: optional parameter specifying the number of processes to be used in an MPI simulation. MPI is not used if this parameter is left at ots default value  None.
        mpirun: optional parameter giving the name of the executable used to laucnh MPI applications. The default is 'mpirun'
    """
    global __runapplication_std_options, __batchq_available, __runapplication_std_queue
    if not __batchq_available and background:
        raise BaseException("BatchQ is not available. Please install it.")
    cmdline = []
    if MPI != None:
        cmdline += [mpirun,'-np',str(MPI)]
    cmdline += [appname]
    if MPI != None:
        cmdline += ['--mpi']
        if appname in ['sparsediag','fulldiag','dmrg']:
            cmdline += ['--Nmax','1']
    cmdline += [parmfile]
    if Tmin:
      cmdline += ['--Tmin',str(Tmin)]
    if Tmax:
      cmdline += ['--TMax',str(TMax)]
    if writexml:
      cmdline += ['--write-xml']

    if background and queue is None:
        if __runapplication_std_queue is None:
            conf = copy.deepcopy(__runapplication_std_options)
            conf.update({"working_directory": os.getcwd() })
            __runapplication_std_queue = LocalShell(**conf)
        queue = __runapplication_std_queue

    if not queue is None:
        input_hash = hash_filelist([parmfile])
        conf = copy.deepcopy(__runapplication_std_options)
        conf.update({'command': " ".join(cmdline), 'overwrite_submission_id': input_hash})
        queue = queue.create_job( **conf )
        col = Collection([queue])
        if not col.submitted() or force_resubmit:
            col.clean()
            col.submit()
        elif col.finished():
            col.recv()
        
        __runapplication_std_queue = queue
        return col
    
    raise BaseException("Please provide a queue or a descriptor as arugment of runApplicationBackground.")


