Remote Jobs using Django
========================
The following briefly explains how to put up a local Django webinterface
and how to synchronise it with jobs submitted to a server. No particular
knowledge of Django is required, except if you wish to setup a permanent
web server for keeping track of jobs states.

Dependencies and preliminary notes
----------------------------------
The web interface depends on Django 1.3 (or newer) which can be 
obtained using easy_install as follows

.. code-block:: bash

   easy_install django

The web interface can be located in any directory. We will in the following 
assume that it is located in ~/remoteweb/.


Starting a local server
-----------------------
Open bash and execute following commands:

.. code-block:: bash

   cd ~/remoteweb/
   python manage.py syncdb
   python manage.py runserver

This will start the local web server which can be accessed 
on the address http://localhost:8000/. In order to synchronise the jobs
from a given server simply type


.. code-block:: bash

   python mange.py update_database [appName [server[:port]]]
   
where [appName] is 'remoteJobs-vistrails' if you are using VisTrails with
the standard settings and [server] is the name of the server. If no
server is supplied the script will assume that you wish to work on the
local machine. If a server name is supplied the script will prompt for
username and password. After entering these the database is updated with
the jobs which has previously been submitted to the server.


Webinterface
------------
In order to access the web interface go to http://localhost:8000/ in
your favorite browser. A list of should now appear

.. image::TODO

which has been optimised for running on mobile units. From the
webinterface you can see the status of your jobs, cancel or
resubmit them. The changes take effect whenever 

.. code-block:: bash

   python mange.py update_database [appName [server[:port]]]

has been executed.
