try:
    from pyalps.tools import executeCommand
except:
    raise BaseException("You need ALPS to import this package.")    

from batchq.queues import NoHUPSSH, LSFBSub
from batchq.core.batch import load_queue, DescriptorQ
from batchq.core.utils import hash_filelist
import copy
#from batchq.core.batch import DescriptorQ
def runApplicationBackground(appname, parmfile, Tmin=None, Tmax=None, writexml=False, MPI=None, mpirun='mpirun', queue=None, descriptor=None, force_resubmit = False):
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


    if not queue is None or not descriptor is None:
        input_hash = hash_filelist([parmfile])
        if not descriptor is None:
            desc = copy.copy(descriptor)
            desc.update_configuration({'input_directory': ".", 'output_directory': ".", 'command': " ".join(cmdline), 'overwrite_submission_id': input_hash})
        else:
            desc = DescriptorQ(queue,  {'input_directory': ".", 'output_directory': ".", 'command': " ".join(cmdline), 'overwrite_submission_id': input_hash} )

        if not desc.wasstarted() or desc.failed() or force_resubmit:
            if desc.failed():
                print "Your last submission FAILED running: "," ".join(cmdline)
            desc.clean()
            desc.submit()
        elif desc.finished():
            desc.recv()


        return desc
    
    raise BaseException("Please provide a queue or a descriptor as arugment of runApplicationBackground.")


