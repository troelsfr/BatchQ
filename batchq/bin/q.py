from batchq.queues import *
from batchq.core.batch import load_settings
import sys
import inspect
import json
import copy

class Main(object):
    """
    The command line tool can be used for queuing and templating. The
    general syntax: 
    
    $ q name [task] [arg1] [arg2] ... [argN] [-u] [-t] [-i] [--parameter1=value1] [--parameter2=value2] ... [--parameterM=valueM]

    $ q name [arg1] [arg2] ... [argN] [-t] [--parameter1=value1] [--parameter2=value2] ... [--parameterM=valueM]
   
    Example:
    $ q nohup-ssh submitjob --host=localhost --username=tfr --indir=. --outdir=/Users/tfr/Downloads/
    
    
    If the name is both a queue name and a template name, the queue will be
    executed as default. For queues the parameters are set in an instance of
    the object, where as for templates these are passed on as context
    variables. If the flag -t is on, the name is looked up as a template.
        
    """

    def __call__(self, name,task=None, *args, **kwargs):
        """

        """
        from batchq.core.library import Library
        which = -1
        u,t,i,q,f = False,False,False,False,True

        if not task is None and "@" in task:
            task, conffile = task.split("@")

            newargs,  newkwargs, switches = load_settings(conffile)
            u,t,i,q,f = switches
            if len(args)< len(newargs):
                for n in range(0,len(args)):
                    newargs[n] = args[n]
                args = tuple(newargs)

            newkwargs.update(kwargs)
            kwargs = newkwargs



        if 'u' in kwargs:
            u = kwargs['u']
            del kwargs['u']
            self.update()
        if 'i' in kwargs:
            i = kwargs['i']
            del kwargs['i']
        if 't' in kwargs:
            t = kwargs['t']
            del kwargs['t']
        if 'q' in kwargs:
            q = kwargs['q']
            del kwargs['q']
            if t:
                raise BaseException("Either of -t or -q must be set, not both.")
        if t or q:
            f = False

        if t and name in Library.templates.dict:
            which = 2
        elif q and name in Library.queues.dict:
            which = 1
        elif name in Library.functions.dict:
            which = 0
        elif name in Library.queues.dict:
            which = 1
        elif name in Library.templates.dict:
            which = 2


        if which == -1:
            print inspect.getdoc(self.update)
            print
            print "Available functions:", ", ".join([a for a in Library.functions.dict.iterkeys()])
            print "Available queues:", ", ".join([a for a in Library.queues.dict.iterkeys()])
            print "Available templates:", ", ".join([a for a in Library.templates.dict.iterkeys()])
            print
            return -1


        switches = (u,t,i,q,f)
        if which == 0:
            fnc = Library.functions.dict[name]            
            fnc(task, args, kwargs, switches)
        
        if which == 1:


            cls = Library.queues.dict[name]
            try:
                if i:
                    kwargs['q_interact'] = True
                instance = cls(*args,**kwargs)
            except:
                if inspect.getdoc(cls):
                    print inspect.getdoc(cls)
                    print
                print "Unexpected error:", sys.exc_info()[0]
                raise


            if hasattr(instance, task):

                fnc = getattr(instance,task)
                r = fnc()
                ret = r.val()
                if type(ret) is not int:
                    print ret
                try:
                    ret = int(ret)
                except:
                    ret = 0
                return ret
            else:
                if inspect.getdoc(cls):
                    print inspect.getdoc(cls)
                    print
                raise BaseException("Task '%s' is not defined for %s." %(task,name))
            return 0

        if which == 2:
            outfile = args[0]

            f = open(task, "r+")
            input = f.read()
            f.close()
            eng = Library.templates.dict[name]

            ins = eng(input)
            ins.set_filename(task)
            output = ins.render({})

            f = open(outfile, "w")
            f.write(output)
            f.close()


            return 0


    def update(self):
        """
        If a listed module is not available, call q with the update
        option -u:

        $ q.py name [task] -u [-i] [--parameter1=value1] [--parameter2=value2] ... [--parameterN=valueN]

        This will update the cache and locate new modules. NOTE: At the
        moment no cache is installed so you really don't need to worry
        about this.
        """
        pass

if __name__ == "__main__":
    main = Main()
    ret = -1
#    try:
    lst = sys.argv

    indices = [i for i in range(0, len(lst)) if len(lst[i])==0 or lst[i][0] !="-"]
    indices.reverse()
    noparam = [lst.pop(i) for i in indices]
    noparam.reverse()

    try:
        file, name, task = noparam[0:3]
        args = noparam[3:]
    except:
        task = None
        file, name = noparam[0:2]
        args = () 

    fnc = lambda x: x[2:].split("=",) if len(x) > 2 and x[0:2] ==  "--" else (x[1:], True)
    kwargs = dict([fnc(val) for val in lst ])
    
    ret = main(name,task,*args, **kwargs)
#    except:
#        print "BatchQ"
#        print "by Troels F. Roennow, 2011-2012 ETH Zurich"
#        print 
#        print inspect.getdoc(main)
#        print
    sys.exit(ret)


    
