Introduction
============
BatchQ is a set of classes written in Python which aim toward
automating all kinds of task. BatchQ was designed for interacting with
terminal application including Bash, SSH, SFTP, Maple, Mathematica,
Octave, Python and more. If for one or another reason your favorite
application is not supported BatchQ is easily extended to support more
programs. 

Dependencies and compatibility
------------------------------
Currently BatchQ only depends on the libraries shipped with Python. It
should therefore work out of the box.

Please note that at the present moment BatchQ has only been tested with
Python 2.7 on Mac OS X 10.6 and with Python 2.6.5 on Ubuntu 10.10.



Installation
------------
There are currently two ways of installing BatchQ. Either you use setup
tools in which case you write

.. code-block:: bash

   easy_install batchq

Alternatively you can download the latest version from GitHub (`.zip`_,`.tar.gz`_) and
install using setup.py

.. code-block:: bash

   cd [location/of/source]
   python setup.py install [ --user | --home=~ ]

The ``--user`` and ``--home``  flags are optional and are intended for
users who do not have write access to the global system. More
information can be found the `Python install page`_.

To test your installation type:

.. code-block:: bash
   
   q help

If a help message is displayed you are ready to go on and submit your
first job.

.. _`.tar.gz`: https://github.com/troelsfr/BatchQ/tarball/master
.. _`.zip`: https://github.com/troelsfr/BatchQ/zipball/master
.. _`Python install page`: http://docs.python.org/install/index.html

Manual installation from GitHub
-------------------------------
The manual installation is intended for development purposes and for
persons who do not want to rely on the install script:

.. code-block:: bash

   export INSTALL_DIR=~/Documents       # Change if you want another install location 
   cd $INSTALL_DIR
   git clone https://github.com/troelsfr/BatchQ.git
   echo export PYTHONPATH=\$PYTHONPATH:$INSTALL_DIR/BatchQ/ >> ~/.profile
   echo export PATH=\$PATH:$INSTALL_DIR/BatchQ/batchq/bin >> ~/.profile

Note that ``.profile`` may be named differently on your system,
i.e. ``.bashrc`` or ``.profilerc``. Start a new session of bash and
write 

.. code-block:: bash
   
   q list

If a list of available commands is displayed, you have successfully installed BatchQ.




Note for Windows users
----------------------
This version of BatchQ is not yet supported on Windows
platforms. Developers are encouraged to extend the ``Process``
module. Unfortunately, it seems that it is not possible to create a
pure Python solution and a terminal module should be written in C/C++.

For information on the structure of the code please consult the
developers introduction.
