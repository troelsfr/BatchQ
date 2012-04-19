from os import path
import json
def create_configuration(filename, args, kwargs, switches):
    """
    

    If invoked from Python, this function takes four arguments
    ``filename``, ``args``, ``kwargs`` and ``switches``.
    """
    if "global" in kwargs:
        del kwargs['global']
        home = path.expanduser("~")        
        f = open(path.join(home,".batchq/configurations/",filename), "w")
    else:
        f = open(filename, "w")
    f.write(json.dumps( (args, kwargs, switches) ) )
    f.close()


from batchq.core.library import Library
def list(module, *args, **kwargs):
    """
    To list the available modules type:

    .. code-block:: bash

       $ q list [argument]

    The optional list argument should be either of module classes (in
    plural): functions, queues, pipelines or templates, i.e.,

    .. code-block:: bash

       $ q list functions

       Available functions:
         configuration
         list
         help

    The list command can also be used without argument in which case it
    produces a list of all available modules. 

    Note this function is not intended for Python use. Insted import
    ``batchq.core.library.Library`` and access the members
    ``functions``, ``queues``, ``templates`` and ``pipelines``.
    """
    print
    if not module is None:
        module = module.lower()
        if hasattr(Library,module):
            print "Available %s:" %module
            x = getattr(Library,module)
            print "  "+"\n  ".join([a for a in x.dict.iterkeys()])
        else:
            print "Module class '%s' not found." % module
        print
    else:
        print "Available functions:"
        print "  "+"\n  ".join([a for a in Library.functions.dict.iterkeys()])
        print
        print "Available queues:"
        print "  "+"\n  ".join([a for a in Library.queues.dict.iterkeys()])
        print
        print "Available pipelines:"
        print "  "+"\n  ".join([a for a in Library.pipelines.dict.iterkeys()])
        print
        print "Available templates:"
        print "  "+"\n  ".join([a for a in Library.templates.dict.iterkeys()])
        print


import inspect
def help(name, *args, **kwargs):
    """
    The help function provides information, if available, about how a
    module is used. The help function is invoked by writing

    .. code-block:: bash

       $ q help [module name]

    Writing 

    .. code-block:: bash

       $ q help help
    
    gives information about the help module (i.e. the information you
    are reading now).
    """
    docs = "No help information present."
    if name is None or name == "":
        name = "help"
    if name in Library.functions.dict:
        print
        print "Function"
        print
        _docs = inspect.getdoc(Library.functions.dict[name])

        if _docs and _docs.strip() != "": docs = _docs
        print "  "+"\n  ".join(docs.split("\n"))
        print
    if name in Library.queues.dict:
        print
        print "Queue"
        print
        _docs = inspect.getdoc(Library.queues.dict[name])
        if _docs and _docs.strip() != "": docs = _docs
        print "  "+"\n  ".join(docs.split("\n"))
        print
    if name in Library.templates.dict:
        print
        _docs = inspect.getdoc(Library.templates.dict[name])
        if _docs and _docs.strip() != "": docs = _docs
        print "Template"
        print
        print "  "+"\n  ".join(docs.split("\n"))
        print
    if name in Library.pipelines.dict:
        print
        _docs = inspect.getdoc(Library.pipelines.dict[name])
        if _docs and _docs.strip() != "": docs = _docs
        print "Pipeline"
        print
        print "  "+"\n  ".join(docs.split("\n"))
        print


import SocketServer
import socket
import sys

def server(pipeline,  args, kwargs, switches):
    print pipeline
    port =  args[0]
    pipeline = Library.pipelines.dict[pipeline]()
    
    class PipelineServer(SocketServer.BaseRequestHandler):
        _pipeline = pipeline
        def handle(self):
            data = self.request[0].strip()
            socket = self.request[1]
            print "Got input from {}:".format(self.client_address[0])
            print data
            response = self._pipeline.send_command(data)
            print self._pipeline.buffer
            socket.sendto(response, self.client_address)


    HOST, PORT = "localhost", int(port)
    server = SocketServer.UDPServer((HOST, PORT), PipelineServer)
    server.serve_forever() 


def client(cmd, args, kwargs, switches):
    HOST, PORT = "localhost", 12345
    

    if cmd is None:
        if not "infile" in kwargs:
            raise BaseException("You must either specify a file or a command.")
        f = open( kwargs['infile'], "r" )
        cmd = f.read()
        f.close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.sendto(cmd , (HOST, PORT))
    # TODO: Fix to arbitrary bytes
    received = sock.recv(1024)
    print received

    sock.close()
