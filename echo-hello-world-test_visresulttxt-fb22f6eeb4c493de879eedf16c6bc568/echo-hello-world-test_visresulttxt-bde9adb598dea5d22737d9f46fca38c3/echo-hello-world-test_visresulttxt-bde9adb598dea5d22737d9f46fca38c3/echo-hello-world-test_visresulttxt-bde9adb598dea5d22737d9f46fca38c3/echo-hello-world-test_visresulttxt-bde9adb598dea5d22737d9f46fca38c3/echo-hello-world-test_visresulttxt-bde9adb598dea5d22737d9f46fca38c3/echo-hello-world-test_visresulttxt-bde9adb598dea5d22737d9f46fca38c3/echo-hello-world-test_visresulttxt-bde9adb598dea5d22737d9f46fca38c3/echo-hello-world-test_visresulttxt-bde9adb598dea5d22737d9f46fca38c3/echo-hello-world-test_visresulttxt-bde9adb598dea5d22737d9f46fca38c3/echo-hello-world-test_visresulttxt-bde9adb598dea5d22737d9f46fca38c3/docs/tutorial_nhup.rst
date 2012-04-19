Tutorial: nohup Remote Submission
=================================
In this tutorial we are going to write a submission module using
nohup. Actually, we will not use nohup itself as this is a rather
unstable application, but instead we will use the bash equivalent
``([command] )`` as this is a much more stable method.


Basic functionality
-------------------
By now we have already written the first many small classes using
BatchQ and therefore, the only thing we really need to know is which
parameters the class should depend on and which methods we should
implement. 

A nohup module should take a command as input
parameter as well as a working directory. It should implement the
methods startjob, isrunning and clean. Subsequently, these function
would need a function that enters the working directory and a function
that checks whether a process is running. The implementation is straight
forward:

.. literalinclude:: ../batchq/contrib/examples/tutorial3_nohup1.py


Full functionality
------------------

