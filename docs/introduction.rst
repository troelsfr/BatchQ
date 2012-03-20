Introduction
============
BatchQ is a set of classes written in Python which aims towards
automating all kinds of task. BatchQ was designed for interacting with
terminal application including Bash, SSH, SFTP, Maple, Mathematica,
Octave, Python and more. If for one or another reason your favorite
application is not supported BatchQ is easily extended to support more
programs. 

Dependencies and Compatibility
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

Alternatively you can download the latest version from GitHub and
install using setup.py

.. code-block:: bash

   cd [location/of/source]
   python setup.py install

That's it.

Note for Windows users
----------------------
This version of BatchQ is not yet supported on Windows
platforms. Developers are encouraged to extend the ``Process``
module. Unfortunately, it seems that it is not possible to create a
pure Python solution and a terminal module should be written in C/C++.

For information on the structure of the code please consult the
developers introduction.
