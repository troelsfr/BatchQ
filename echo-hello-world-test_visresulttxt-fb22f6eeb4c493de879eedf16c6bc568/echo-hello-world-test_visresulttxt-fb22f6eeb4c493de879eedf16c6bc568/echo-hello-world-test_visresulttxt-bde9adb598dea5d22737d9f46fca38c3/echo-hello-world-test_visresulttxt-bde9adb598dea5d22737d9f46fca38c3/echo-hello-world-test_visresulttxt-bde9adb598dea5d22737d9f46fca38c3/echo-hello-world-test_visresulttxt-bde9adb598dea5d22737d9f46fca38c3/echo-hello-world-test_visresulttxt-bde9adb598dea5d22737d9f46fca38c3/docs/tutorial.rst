Developer: Getting started
==========================
The following section is meant as an instructive example of how BatchQ
can be used to automate simple tasks such as logging on to a server and
creating a configuration file. This first section is somewhat basic
stuff, but important, nevertheless, since BatchQ is designed to be
different from your normal Python programs in its structure. All the key
classes are shortly described here. 

Imagine that you want to open Bash, go to  Documents in your home folder
and create a text file. With Bash commands for this would be 

.. code-block:: bash

   cd ~/Documents
   echo Hello world > hello.txt

In this tutorial we will automate this task. If you are eager to use
BatchQ and do not really care about the 
underlying functionality you probably should skip right away to one of
the examples of job automation:

1.  :ref:`example-createfile1`
2.  :ref:`example-createfile2`
3.  :ref:`example-createfile3`

However, it is strongly recommended that you go through all the examples
to get a basic understanding of the structure of BacthQ, how it works
and what you can do with it.

Processes and Pipes
-------------------
While it is not necessary to understand the concepts of Processes and
Pipes in order to use BatchQ, it surely is useful in order to get a
picture of the whole structure of this package.
If you are familiar with `Pexpect <http://www.noah.org/wiki/pexpect>`
you are already familiar with some of the key concepts of BatchQ. BatchQ
provides a classes which have some similarities with Pexpect, yet
differs in a number of ways, the most significant being that BatchQ
communication with the terminal and expect functionality has been
seperated into two classes: Process and BasePipe. The Process class
provides methods for communicating directly with a process with no
intepretation of the output, whereas BasePipe implements output
interpretation and expect functionality.


Unlike Pexpect, Process does not apply which on the command passed as
the constructor argument and this command must be applied manually. In
the following example we open a instance of Bash writes "echo Hello
world" and read the output:

.. literalinclude:: ../batchq/contrib/examples/core_process.py

This code produces following output 

.. literalinclude:: ../batchq/contrib/examples/core_process.output

Here we are essentially communicating with the process at the most basic
level and we have to interpret every character returned. Especially, it
should be noted that escape characters are not interpreted in any way
and also that the response from x.read() contains the echo of the
command. Both of these features are somewhat inconvenient when ones to
communicate with a process.

The BasePipe class overcome the inconvenience of the Process class by
implementing expect 

.. literalinclude:: ../batchq/contrib/examples/core_basepipe.py

which produces

.. literalinclude:: ../batchq/contrib/examples/core_basepipe.output

The properties pipe and pipe_buffer are references to the Process object
and the Process.buffer, respectively. As with the first example we see
that the process buffer contains VT100 characters. However, the BasePipe
uses a VT100 interpreter to ensure that the output in BasePipe.buffer
looks like what you would see if you where interacting with a terminal
yourself. This is important as it eases the development process of
pipelines. 

The separation of Process and BasePipe ensures that unsupported
platforms in the future can be supported. In order to make BatchQ work
on unsupported system (i.e. Windows at the moment) one has to write a
new Process module for the platform. Once a Process class exists
BasePipe implements all the features needed to efficiently communicate
with an instance of a process.


Pipelines
+++++++++
Pipelines are subclasses of BasePipe which are intended for a specific
program like the example in the previous section. BatchQ is shipped with
many different pipelines found in batchq.pipelines which among others
contain BashTerminal, SSHTerminal and SFTPTerminal. The SSHTerminal
subclasses BashTerminal and replaces the process instance with an SSH
instance. This in term means that any program written for BashTerminal
works with SSHTerminal which is handy as you might want to develop a
program locally and once working, deploy it using SSH.

We are going to give an example of how this is done in the following
code:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_python_implementation.py

With this code we have solved the initial problem, and moreover, the
code is easily extended to support SSH by subclasssing 
CreateFileBash and replacing the terminal:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_python_implementation_SSH.py
   :lines: 2-

This clearly demonstrates the power of using a standards for the various
terminal implementations. The function calls used here would be also be
possible to implement on a Windows machine, and thus, in this way we
have a universal script that works independent of the system it is
on. 


BatchQ Basics
-------------
Next to the pipelines and processes, the BatchQ module contains
five other important classes: BatchQ, WildCard, Property, Controller and
Function.
BatchQ is the general model which your class should inherit. It provides
the functionality for manging pipelines, properties, and function
queues. In short, any BatchQ script is a class that subclasses BatchQ
and have one or more of WildCard, Property, Controller and
Function defined. The general structure of a BatchQ class is

.. literalinclude:: ../batchq/contrib/examples/tutorial2_basestructure.py
   :linenos:

Properties are input parameters for the automation model you are
creating, controllers are pipeline holders and functions are queues of
function calls that will be invoked on the class through the
controller. Thus, calling ``SubmissionModel().t1_fnc2()`` would result in
two function calls: ``instance.a()`` and ``instance.b()`` with
``instance = Class1(arg1, arg2, ...)``. It is possible to use
the parameters as function arguments as done in line 14. Upon
realisation of the function calls ``param1`` and ``param2`` are
fetched. They may be changed using the normal assignment operator before
the function call to change their value. Get an idea how this works we
will in the following go through some simple examples.


Example: Hello world
++++++++++++++++++++
In this example we demonstrate how a function queue is invoked on the
pipeline:


.. literalinclude:: ../batchq/contrib/examples/tutorial2_hello_world.py

This code results in following output

.. literalinclude:: ../batchq/contrib/examples/tutorial2_hello_world.output

What happens is:

1. A controller is defined which creates an instance ``pipe`` of the
   Pipeline class.
2. Next a function ``fnc`` is defined as the sequence of function calls
   ".hello_world(), .hello_batchq()"
3. When ``fnc`` is called two function calls, ``pipe.hello_world()`` and
   ``pipe.hello_batchq()`` are made.

It is worth noting that the function queue is abstract, meaning that the
queue accept any calls - errors will first occur when ``instance.fnc()``
is called.

Example: Hello parameter
++++++++++++++++++++++++
Next we extend the previous program introducing a parameter 

.. literalinclude:: ../batchq/contrib/examples/tutorial2_hello_param.py

Three lines of output are produces here:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_hello_param.output

each corresponding to a call to ``fnc()``. This code shows how a
parameter can be passed on to a function call. It is important to notice
that the parameter can be changed even after creating an instance of an
object and that properties are *not* static members of the class,
i.e. different instances may have different values. Finally, it is worth
noticing that properties becomes constructor arguments of the BatchQ
subclass.  

Example: Hello error I
++++++++++++++++++++++
The default of BatchQ is that all errors raised are suppressed by the
Function queue. You can, however, force BatchQ to raise errors by
setting the parameter ``verbose`` of the function object:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_error1.py


Example: Hello error II
+++++++++++++++++++++++
The BatchQ function also is given the possibility to raise errors. It is
done in the following way:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_error2.py

The ``throw`` function ignores the ``verbose`` option on the ``Function``
object and is always thrown.

Example: Function Inheritance
+++++++++++++++++++++++++++++
Common jobs such as changing into a working directory is often done in
several procedures when making a batch script. For this reason BatchQ
allows you to inherit earlier defined functions

.. literalinclude:: ../batchq/contrib/examples/tutorial2_inherit.py

Upon inheritance the entire queue from ``fnc1`` is copied meaning that
the result stack of ``fnc1`` is not populated as it would have been with
a function call.

Example: Function Calls
+++++++++++++++++++++++
Often it is useful to divide jobs into subprocedures. For this purpose
it can often be necessary to do function calls. Function calls are also
allowed with  BatchQ

.. literalinclude:: ../batchq/contrib/examples/tutorial2_call.py

One important thing to note here is that it is the Function object that
is passed on as argument and not Function(). The reason is that we are
creating a reference model, the queue, and not performing an actual call
during the construction of the class.


Wildcards
+++++++++
TODO: Explain the concept of a wildcard

In the following example we define five different wild cards.
The first wildcard _ pops the result stack and the second _r pops the
result stack in reverse order - that is, if _, _ produces "a", "b", then
_r, _r produces "b","a".

.. literalinclude:: ../batchq/contrib/examples/00f_wildcards.py


.. _example-createfile1:

Example: CreateFile
+++++++++++++++++++
At this point we have significantly insight into the structure of BatchQ
to write a realisation of the initial problem: creating a script that
creates a directory:

.. code-block:: python

   from batchq.core import batch
   from batchq.pipelines.shell.bash import BashTerminal
   from batchq.pipelines.shell.ssh import SSHTerminal

   class CreateFile1(batch.BatchQ):
     _ = batch.WildCard()

     directory = batch.Property()
     command = batch.Property()

     terminal = batch.Pipeline(BashTerminal)
    
     create_file = batch.Function() \
         .home().chdir(_) \
         .chdir(directory).send_command(command)

     instance = CreateFile1("Documents", "echo hello world > hello.txt")
     instance.create_file()

While this code is short and very easy to read, it obviously have shortcomings:
The code will fail if the directory does not already exist. In order to
resolve this issue we need to use some built-in functions to do simple
if statements.

Built-in Do-function
++++++++++++++++++++

.. _example-createfile2:

Example: CreateFileAndDirectory
+++++++++++++++++++++++++++++++
With the ``do`` we can now extend our previous script and ensure that
the directory is created if it does not exist:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_create_file2.py



Example: Short version
++++++++++++++++++++++
While the previous code is pretty taking into consideration what it
does it can still be made shorter. One of the neat features of function
queues are that you can predefine certain patterns - as for instance
creating a directory in your home directory:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_create_file3.py



Overwriting Controllers
+++++++++++++++++++++++
A key feature of BatchQ is that you can overwrite controllers from your
previous models. This means that once you have made a model for one
pipeline you can use it on another one by simply overwriting the
controller. In the following we overwrite the controller for one
pipeline with a new controller for another pipeline:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_replacement.py

The replacement pipeline reverses the string and the code produces the
following output 

.. literalinclude:: ../batchq/contrib/examples/tutorial2_replacement.output



.. _example-createfile3:

Example: CreateFileSSH
++++++++++++++++++++++
Clearly, the previous example comes in handy when we want to extent our
script to support SSH:

.. literalinclude:: ../batchq/contrib/examples/tutorial2_create_file4.py
   :lines: 3-

The three new properties are appended to the constructor arguments.
