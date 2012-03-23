Users Guide
===========


In the following we will refer to a tool called ``nohup``. This name is
missleading as we do not use the actual nohup tool for several reasons,
the most significant being that nohup some times hangs up. Instead we
start a background job in a subshell, i.e.

.. code-block:: bash

   $ (./job_name parameters & )

This essentially have the desired effect, namely that the program does
not hang up when the shell is closed. Throughout this document we will
refer to this as ``nohup`` rather than ``starting a background job in a
subshell``. For more information on nohup alternatives see `What to do when nohup hangs up anyway`_.



.. _`What to do when nohup hangs up anyway`: http://linuxshellaccount.blogspot.com/2007/12/what-to-do-when-nohup-hangs-up-anyway.html


Quick start
-----------
This section is intended for getting you started quickly with BatchQ and
consequently, few or no explanations of the commands/scripts will be
given. If you would like the full explanation on how BatchQ works, skip
this section. If you choose to read the quick start read all of it no
matter whether you prefer Python over bash.

Command line
++++++++++++
First you need to create configurations for the machines you want to
access. This is not necessary, but convenient (more details are given in
the following sections). Open ``bash`` and type

.. code-block:: bash

   $ q configuration my_server_configuration  --working_directory="Submission" --command="./script"  --input_directory="." --port=22 --server="server.address.com" --global
   $ q configuration your_name  --username="your_default_used"  --global


In the above change the ``server.address.com`` to the server address you
wish to access. Also, change the ``username`` in the second line to your
default username. Next, create a new director ``MyFirstSubmission`` and 
download the script ``sleepy``

.. code-block:: bash

   mkdir MyFirstSubmission
   cd MyFirstSubmission
   wget http://downloads.nanophysics.dk/scripts/sleepy
   chmod +x sleepy

The job ``sleepy`` sleeps for 100 seconds every and for every second it
echos "Hello world". Submit it using ``server.address.com`` using the
command:

.. code-block:: bash

   $ q [batch_system] job@my_server_configuration,your_name --command="./sleepy"

Here ``batch_system`` should be either ``nohup``, ``ssh-nohup`` or ``lsf``.
Check the status of the job with

.. code-block:: bash

   $ q [batch_system] job@my_server_configuration,your_name --command="./sleepy"
   Job is running.

And after 100s you get

.. code-block:: bash

   $ q [batch_system] job@my_server_configuration,your_name --command="./sleepy"
   Job has finished.
   Retrieving results.

At this point new files should appear in your current directory:

.. code-block:: bash

   $ ls
   sleepy   sleepy.data

In order to see the logs of the submission type

.. code-block:: bash

   $ q [batch_system] stdout@my_server_configuration,your_name --command="./sleepy"
   This is the sleepy stdout.
   $ q [batch_system] stderr@my_server_configuration,your_name --command="./sleepy"
   This is the sleepy stderr.
   $ q [batch_system] log@my_server_configuration,your_name --command="./sleepy"
   (...)

The last command will differ depending on which submission system you
use. Finally, we clean up on the server:

.. code-block:: bash

   $ q [batch_system] delete@my_server_configuration,your_name --command="./sleepy"
   True

Congratulations! You have submitted your first job using the command
line tool.


Python 
++++++
Next, open an editor, enter the following Python code:


.. code-block:: python

   TODO

and save it as ``job_submitter.py`` in ``MyFirstSubmission``. Go back to
the shell and type:

.. code-block:: python

   $ python job_submitter.py

And there you go. Your second submission was done with Python.


Multiple nodes
++++++++++++++
Each submission module provides the parameters ``processes``,
``wall``, ``openmp_threads``, ``mpi``, ``max_memory`` and
``max_space`` which can be used to specify how a given process should
run. At the moment changing these parameters only affect the ``lsf``,
but in future releases ``nohup`` and ``nohup-ssh`` will also be affected.



Using the command line tool
---------------------------
The following section will treat usage of BatchQ from the command
line. 


Available modules
+++++++++++++++++
The modules available to BatchQ will vary from system to system
depending on whether custom modules have been installed. Modules are
divided into four categories: functions, queues, pipelines and
templates.
The general syntax of the Q command is:

.. code-block:: bash

   $ q [function/queue/template] [arguments]

The following functions are available through the console interface and
using Python and are standard modules included in BatchQ which provides
information about other modules

.. autofunction:: batchq.queues.functions.list

.. autofunction:: batchq.queues.functions.help



Submitting jobs
+++++++++++++++
The BatchQ command line interface provides you with two predefined
submission modules: ``nohup`` and ``lsf``. ``nohup`` is available on every 


To submit a job type:

.. code-block:: bash

   $ cd /path/to/input/directory
   $ q lsf submit -i --username=user --working_directory="Submission" --command="./script" --input_directory="." --port=22 --server="server.address.com"

The above command will attempt to log on to ``server.address.com`` using
the username ``user`` through port 22. It then creates a working
directory called ``Submission`` in the entrance folder (usually your
home directory on the server) and transfer all the files from your
``input_directory`` to this folder. The ``command`` is then submitted to
``lsf`` and the SSH connection is terminated.


Once you have automated the submission process you want to store the
configuration parameters in a file in order to shorten the commands need
to operate on your submissions. Using the example from before, this can
be done as

.. code-block:: bash

   $ q configuration brutus -i --username=user --working_directory="Submission" --command="./script" --input_directory="." --port=22 --server="server.address.com"

The above code creates a configuration named "brutus" which contains the instructions for submitting your job on "server.address.com".
Having created a configuration file you can now submit jobs and check status with 

.. code-block:: bash
   
   $ q lsf submit@brutus
   True
   $ q lsf pid@brutus
   12452

This keeps things short and simple. You will need to create a
configuration file for each server you want to submit your job. If for
one or another reason you temporarily want to change parameters of your
configuration, say the ``working_directory``, this can be done by adding
a long parameter:

.. code-block:: bash
   
   $ q lsf submit@brutus --working_directory="Submission2"
   True

You can configure Batch Q command line tool with several input configurations

Checking the status of a job, retrieving results and deleting the
working directory of a simulation is now equally simple

.. code-block:: bash
   
   $ q lsf status@brutus
   DONE

   $ q lsf recv@brutus
   True

   $ q lsf delete@brutus
   True

The retrieve command will only retrieves files that does not exist, or
differs from those in the input directory.



Finally, the Q system implements a fully automated job submission
meaning that the system will try to determine the state of you job and
take action accordingly. For fast job submission and status checking
write:

.. code-block:: bash
   
   $ q lsf job@brutus,config
   Uploading input directory.
   Submitted job on brutus.ethz.ch

   $ q lsf job@brutus,config
   Job pending on brutus.ethz.ch

   $ q lsf job@brutus,config
   Job running on brutus.ethz.ch

   $ q lsf job@brutus,config
   Job finished on brutus.ethz.ch
   Retrieving results.
   
   Do you want to remove the directory 'Submission2' on brutus.ethz.ch (Y/N)? Y
   Deleted Submission2 on brutus.ethz.ch


You can equally submit the job on your local machine using ``nohup`` instead
of ``lsf``.




A few words on job hashing
++++++++++++++++++++++++++
When submitting a job Batch Q generates a hash for your job. The hash
includes following:

  * An MD5/SHA sum of the input directory
  * The name of the server to which the job is submitted
  * The submitted command (including parameters)


It is not recommended, nevertheless possible, to overwrite the hash
key. This can be done by adding a
``--overwrite_submission_id="your_custom_id"``. This can be useful in
some cases. For instance you might want to work on your source code
during development. This would consequently changed the MD5 of your
input directory and Batch Q would be incapable of recognising your job
submission. Batch Q is shipped with a configuration for debugging which
can be invoked by

.. code-block:: bash
   
   $ q lsf submit@brutus,debug

The debug configuration is only suitable for debug as the submission id
is ``debug``. 


Another scenario where you may want to change the hashing routine is the
case where you store your output data in your input
directory. Submitting several jobs and pulling results will over time
change the hash of the input directory. To overcome this issue add
``eio`` (short for equal input/output directory) to your configuration

.. code-block:: bash
   
   $ q lsf submit@brutus,eio

The ``eio`` flag will overwrite your ``output_directory`` with the value
of your ``input_directory`` and change the hashing routine to only
include the command and server name.

Example: Submitting ALPS jobs using nohup
+++++++++++++++++++++++++++++++++++++++++


Example: Submitting ALPS jobs using LSF
+++++++++++++++++++++++++++++++++++++++



Example: Submitting multiple jobs from one submission directory
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
In some cases one may not want to copy the same directory several times
to the server as this may take up vast amounts of space. If the
simulation output only depends the command line parameters (as is the
case for ALPS ``spinmc``) one can use the ``eio`` configuration to
submit several commands reusing the same submission directory

.. code-block:: bash
   
   $ q lsf job@brutus,eio --working_directory="Submission" --command="spinmc TODO1"
   $ q lsf job@brutus,eio --working_directory="Submission" --command="spinmc TODO2"
   $ q lsf job@brutus,eio --working_directory="Submission" --command="spinmc TODO3"





Using Python
------------


Submitting jobs
+++++++++++++++

Retrieving results
++++++++++++++++++


Q descriptors, Q holders and Q functions
++++++++++++++++++++++++++++++++++++++++
Batch Q user API is based on three main classes Q descriptors, Q holders (queues)
and Q functions. Usually Q functions are members of instances of Q
holder classes while Q descriptors are reference objects used to ensure
that you do not open more SSH connections than necessary. Descriptors
link a set of input configuration parameters to a given queue. An
example could be:

.. code-block:: python

   class ServerDescriptor(DescriptorQ):
         queue = LSFBSub
         username = "user"
         server="server.address.com"
         port=22
         options = ""
         prior = "module load open_mpi goto2 python hdf5 cmake mkl\nexport PATH=$PATH:$HOME/opt/alps/bin"
         post = ""
         working_directory = "Submission" 

The descriptor ``ServerDescriptor`` implements all Q functions and
properties defined in the class ``LSFBSub``. However, the descriptor
ensures that the all queue parameters are set accordingly to those given
by the descriptor definition before executing a command on the
queue. Therefore, if you have two descriptor instances that shares a queue

.. code-block:: python

   queue = LSFBSub()
   desc1 = DescriptorQ(queue)
   desc1.update_configuration(working_directory = "Submission1")
   desc2 = DescriptorQ(queue)
   desc2.update_configuration(working_directory = "Submission2")

you are ensured that your are working in the correct directory by using
the descriptor instead of the queue directly. 
Notice that in order to update the queue properties using the descriptor
one needs to use ``update_configuration`` rather than
``descriptor.property`` (i.e. ``desc2.working_directory`` in the above
example). The reason for this is that any method or property of a
descriptor object is an "reference" to queue methods and properties. The
only methods that are not redirected are the implemented descriptor
methods:

.. autoclass:: batchq.core.batch.DescriptorQ
   :members:

.. code-block:: python

   desc1 = ServerDescriptor()
   desc2 = ServerDescriptor(desc2)
   desc2.update_configuration(working_directory = "Submission2")


In general, when copying descriptors, make sure to do a shallow copy as
you do not want to make a deep copy of the queue object.


Example: Submitting ALPS jobs using nohup
+++++++++++++++++++++++++++++++++++++++++
The BatchQ package comes with a preprogrammed package for ALPS. This
enables easy and fast scripting for submitting background jobs on local
and remote machines. Our starting points is the Spin MC example from the
ALPS documentation:


.. literalinclude:: ../../batchq/contrib/alps/examples/original.py


Introducing a few small changes the script now runs using BatchQ for
submission:

.. literalinclude:: ../../batchq/contrib/alps/examples/example3_class.py


Executing this code submit the program as a background process on the
local machine. It can easily be extended to supporting SSH and LFS by
changing the queue object:

.. code-block:: python

   # TODO: Give example




Example: Submitting multiple jobs from one submission directory
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



Using VisTrails
---------------


Submitting jobs
+++++++++++++++

Retrieving results
++++++++++++++++++


Example: Submitting ALPS jobs using nohup
+++++++++++++++++++++++++++++++++++++++++


Example: Submitting ALPS jobs using LSF
+++++++++++++++++++++++++++++++++++++++

