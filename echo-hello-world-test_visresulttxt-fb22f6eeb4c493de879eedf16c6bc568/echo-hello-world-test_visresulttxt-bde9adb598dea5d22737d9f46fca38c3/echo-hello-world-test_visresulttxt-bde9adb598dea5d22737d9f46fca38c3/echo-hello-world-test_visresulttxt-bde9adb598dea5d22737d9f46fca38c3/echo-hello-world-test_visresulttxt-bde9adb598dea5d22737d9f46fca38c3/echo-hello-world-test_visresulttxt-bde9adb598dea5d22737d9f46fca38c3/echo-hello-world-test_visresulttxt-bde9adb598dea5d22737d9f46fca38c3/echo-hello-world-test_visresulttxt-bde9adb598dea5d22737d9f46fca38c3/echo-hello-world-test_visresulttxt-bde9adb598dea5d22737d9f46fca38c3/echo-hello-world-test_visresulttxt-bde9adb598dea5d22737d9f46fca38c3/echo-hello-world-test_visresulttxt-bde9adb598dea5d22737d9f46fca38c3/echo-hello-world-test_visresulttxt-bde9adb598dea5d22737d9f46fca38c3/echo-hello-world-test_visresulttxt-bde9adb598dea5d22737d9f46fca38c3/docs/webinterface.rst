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


Remote Jobs with custom database
================================
We will in the following assume that you have a access to a database
with predefined tables and columns. In this part of the document we will
describe how to poll the information from the server and add it to a
database.


Pulling settings entries
------------------------
Pulling the submitted jobs from a server is done using the
RemoteJobSubmitter module.

.. code-block:: python

   from remotejobs import RemoteJobSubmitter
   import getpass
  
   class Database:
      """
      This object will represent our database.
      """
      def get_record(primary_key): 
          """
          This methods returns a record as a dictionary 
          if it is found in the database and None else.
          """
          pass

      def update(primary_key, record_dict):
          """
          This method updates the record with the primary key as
          primary_key by setting key = 'val' for key, val in record_dict. 
          """
          pass

      def insert(primary_key, record_dict):
          """
          This method inserts a record with the primary key as
          primary_key by setting key = 'val' for key, val in record_dict. 
          """
          pass

   server = None
   port = 22
   username = getpass.getuser()
   password = getpass.getpass()

   # We will update to columns in the database: "last_updated" and "id".
   # The following dictionary will be used to map the settings entries 
   # into the database column names.
   mapping = {'updated': 'last_updated', 'jobid': 'id'}

   job_submitter = RemoteJobSubmitter(appName, server, username, password)
   jobs = job_submitter.settings.list_keys()
   db = Database()

   for jobid in jobs:
       hash, n = jobid.rsplit("_",1)
       try:
         n = int(n)
       except: # In case the directory contains non-valid settings files
         continue

       # Remark it is important to put clean (third argument) to False here
       # If this is not set to False any finished job will be deleted.
       record = job_submitter.check_state(hash, n, False)
       
       setting_entries = filter(lambda x: x in mapping, [key for key in records])
       cols = [mapping[key] for key in setting_entries]
       vals = [record[key] for key in setting_entries]
       record_dict = zip(cols, vals)

       if db.get_record(jobid) is None:
          db.insert(jobid, record_dict)
       else:
          db.update(jobid, record_dict)


This code serves as an example and is not recommended to deploy for
pulling the jobs without further optimisations. 
The above example will run slowly due to two 
reasons:

1. There is made no check whether the database record is up-to-date
meaning that we update records that are all up-to-date every time we
check the status of the jobs.

2. As more an more jobs gets submitted to the server the list of key
entries becomes very large. It can therefore be beneficial to clean the
settings module for any keys that has been marked as cleaned. In order
to so add the following to your 

.. code-block:: python

   TODO

cron script.

Be aware that the last optimisation will cause problems if several
databases are updated as a finished job may be deleted before it is pull
into all databases.
