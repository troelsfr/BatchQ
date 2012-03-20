"""
This module implements classes that enables easy reproduction of 

"""
from string import Template
import json
import copy
from os import path
from utils import zipper,hash_filelist
import shutil
import tempfile
import subprocess
import inspect
from batchq.pipelines.shell.bash import format_path
import os
import hashlib
import datetime 

# EXTERNAL
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_mimetype, guess_lexer_for_filename,guess_lexer

class ProvenanceField(object):
    """
    The ``ProvenanceField`` provides the basic functionality of all
    workflow fields. Most importantly it ensures that fields are
    executed in the order they are defined and that dependencies are
    respected.
    """

    __object_counter = 0
    def __init__(self, *args, **kwargs):
        self.__counter__ = ProvenanceField.__object_counter
        ProvenanceField.__object_counter+=1 
        self._value = None
        self._computed = False
        self._dependencies = []
        for a in args:
            if isinstance(a,ProvenanceField):
                self._dependencies.append(a)

        for a in kwargs.itervalues():
            if isinstance(a,ProvenanceField):
                self._dependencies.append(a)

        self._cache_id = None
        self._reporters = []
        self._blocks = None
        self._msg = None
        self._name = "noname"
        self._queue = None
        self._workflow = None 
        self._tmpdir = None 
        self._pwd = None
        self._base_url = "http://localhost/"
        self._nodename = None
        self._section_ids = ("","","")

    def occupy(self, server): # FIXME: check length
        self._reporters[0].occupy(server)

    def isoccupied(self,server):
        return self._reporters[0].isoccupied(server)


    def __call__(self,*args,**kwargs):
        if not  self._queue is None:
            self.execute(self._queue, *args,**kwargs)
            if self.finished():
                self._section_ids = self._reporters[0].section_id()
                return self.value()
            return "## TO BE COMPUTED ##"
            
        raise BaseException("Please set a queue before requesting a task")

    def get_url(self):
        return self._base_url
    def set_url(self, url):
        self._base_url = url
    base_url = property(get_url, set_url)


    def get_pwd(self):
        return self._pwd
    def set_pwd(self, name):
        self._pwd = name
    pwd_directory = property(get_pwd, set_pwd)

    def get_nodename(self):
        return self._nodename
    def set_nodename(self, nodename):
        self._nodename = nodename
    nodename = property(get_nodename, set_nodename)


    def get_tmp(self):
        return self._tmpdir
    def set_tmp(self, name):
        self._tmpdir = name
    temporary_directory = property(get_tmp, set_tmp)


    def get_name(self):
        return self._name
    def set_name(self, name):
        self._name = name
    name = property(get_name, set_name)

    def get_workflow(self):
        return self._workflow
    def set_workflow(self, w):
        self._workflow = w
    workflow = property(get_workflow, set_workflow)


    def get_queue(self):
        return self._queue

    def set_queue(self, q):
        self._queue = q
        if self._nodename is None:
            self._nodename = q.nodename().val().strip()
        q.overwrite_nodename_with = self._nodename
        q.overwrite_nodename()
    queue = property(get_queue, set_queue)


    def reset(self):
        self._computed = False
    
    @property
    def dependencies(self):
        return self._dependencies

    def execute_dependencies(self):
        """
        """
        ret = True
        for d in self._dependencies:
            ret = ret and d.execute()
        return ret 

    def execute(self, queue, *args, **kwargs):
        """
        The ``execute`` function in the ``ProvenanceField`` is a virtual
        function inteded to be overwritten. Essentially, the overwritten
        function implement how a given task is performed using a given
        ``queue``. 
        """
        if self._computed: return self._computed
        self.execute_dependencies()

        return True

    def blocks(self):
        """
        Returns the log blocks generated in the execute function. These
        blocks are eventually passed on to the ``Reporter`` object(s)
        and  cached if ``cacheid`` is different from ``None``.
        """
        return self._blocks

    def cache(self):
        """
        This function generates a cache of the blocks
        """

    def value(self):
        """
        This function 
        """
        if not self._computed:
            return None
        return self._value

    def register_reporter(self, instance):
        self._reporters.append( instance )

    def register_reporters(self, instances):
        self._reporters += instances

    def report(self, id, name, mimetype, contents = None, file = None ):
        for reporter in self._reporters:
            reporter.report(id, name, mimetype, contents, file)

    def log(self, msg=None, coloring=None):
        print msg
        if not msg is None:
            self._msg = msg
        return self._msg

    def reference(self, full = True):
        title1,title2, label = self._section_ids
        url = self.base_url + "#%s" % label
        if full:
            return r"\href{%s}{%s}" % ( url, title2 )
        return r"\href{%s}{%s}" % (url, title1 )


class Submission(ProvenanceField):
    def __init__(self, directory, submission_dir, command, *args, **kwargs):
        self._submission_dir = submission_dir
        self._directory = directory
        self._command = command
        self._finished = False  
        self._hash = ""
        self._cache = {}
        self._loaded_from_cache = False
        self._output_directory = None
        super(Submission, self).__init__(*args, **kwargs)

    def set_output(self, directory):
        self._output_directory = directory

    def load_cache(self,hash):
        queue = self._queue
        if self._output_directory is None:
            raise BaseException("Please set the output directory of '%s'." % (self.name))

        hashfile = path.join(self._directory,".cache_%s" % hash)
        self._hash = hash

        try:
            file = open(hashfile,"r")
            input_settings = json.loads(file.read())
            file.close()
        except:
            input_settings = {'directory': self._directory, 'command':self._command, 'hash':hash,  'output': self._output_directory}

        self._cache = input_settings


        loadcache = False
        if 'output_hash' in input_settings:
            queue.output_directory = self._output_directory
            outhash = queue.hash_output().val()
            if outhash and input_settings['output_hash'] == outhash.strip():
                self._value = self._output_directory
                loadcache = True
            else:
                queue.output_directory = input_settings['output']
                outhash = queue.hash_output().val()
                if outhash and input_settings['output_hash'] == outhash.strip():
                    self._value = input_settings['output']
                    loadcache = True                    
            queue.output_directory = self._output_directory

        self._loaded_from_cache = False
        if loadcache:
            fromcache = True
            cachedir = self._value
            if not self._output_directory == cachedir:
                if os.path.exists(self._output_directory):
                    self.log("Deleting old files in '%s'." % (self._output_directory))
                    shutil.rmtree(self._output_directory)

                self.log("Copying cached files from '%s' (with id '%s') to '%s'." % (cachedir, self._cache['output_hash'],self._output_directory))

                shutil.copytree(cachedir, self._output_directory)
            else:
                self.log("Files in '%s' are up to date." % (self._output_directory))
            self._finished= True
            self._computed = True
            self._loaded_from_cache =True

        return self._loaded_from_cache

    def save_cache(self,hash):
        if self._hash != hash:
            raise BaseException("Please call load_cache for '%s' first to create cache skeleton." % self.name )

        hashfile = path.join(self._directory,".cache_%s" % hash)
        file = open(hashfile,"w")
        file.write(json.dumps(self._cache))
        file.close()

        
        
    def execute(self, queue,  *args, **kwargs): 
        if self._computed: return self._computed
        self.execute_dependencies()

        nodename = self.nodename
#        queue.input_directory = self._directory
#        queue.command = self._command

        self._computed = True
        hash = self._hash 

        if self.isoccupied(nodename):
            self.log("'%s' is currently occupied (%s)." % (nodename, self.name))
            return self._computed

        if 'pid' in self._cache:
            if queue.pending().val():
                self.occupy(nodename)
                self.log("Job with id '%s' is pending on '%s'." % (hash, nodename))                
                return self._computed

            if queue.running().val():
                self.occupy(nodename)
                self.log("Job with id '%s' is still running on '%s'." % (hash,nodename))
                return self._computed

            if queue.finished().val():
                return self._computed

            self.log("Resubmitting job with id '%s' on '%s'." % (hash,nodename))
            queue.submit()
            self.occupy(nodename)
        else:

            self._finished = False  
            self.log("Submitting job with id '%s' on '%s'." % (hash,nodename))

            queue.submit()
            self.occupy(nodename)

        pid = int(queue.pid().val())

        self._cache['start_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._cache['pid'] = pid
        self.save_cache(hash)

        return self._computed

    def finished(self, output_directory):
        queue = self._queue
        if queue is None:
            raise BaseException("Please set a queue before requesting a task for '%s'" % self.name)            

        self._finished = False
        self.set_output(output_directory)

        nodename = self.nodename
        queue.input_directory = self._directory
        queue.working_directory = self._submission_dir
        queue.command =self._command
        hash = queue.hash_input().val()
        self.load_cache(hash)


        if not self._computed:
            self.execute(self._queue)


        queue.output_directory = output_directory

        if not self._finished:
            self._finished = queue.finished().val()

        if not self._finished:
            self.log("Warning: computation '%s' with id '%s' has not finished yet." % (self.name, hash))
        else:
            if not self._loaded_from_cache:
                self.log("Execution '%s' has finished on '%s'." % (self.name, nodename))


            info = queue.system_info().val()
            self.report("machine_profile_%s" % nodename, "machine/profile/%s" % nodename, "application/x-sh", contents = info)         



            # Storing the input for the reporter
            tmpfile = path.join(self.temporary_directory, "%s-%s.zip"%(self.name,hash))
            if not 'reporter_input_file_hash' in self._cache or not self._cache['reporter_input_file_hash'] == hash_filelist([tmpfile]):                
                pwd, dir = self._cache['directory'].rsplit("/",1) # FIXME: Not windows compatible
                if dir.strip() == "":
                    pwd, dir = pwd.rsplit("/",1) # FIXME: Not windows compatible

                self.log("Generating (input) '%s' from '%s'." % ( tmpfile, dir ) )
                zipper(tmpfile, dir, pwd )
                self.workflow.register_temporary_file(tmpfile)
                filehash1 = hash_filelist([tmpfile])
            else:
                filehash1 = self._cache['reporter_input_file_hash']

            dir_hash = queue.hash_input_directory().val()
            self.report("submission_%s" % dir_hash, "submission/input/%s" % self.name, "application/zip", file = tmpfile)

            # Getting the output of the simulation
            if not self._loaded_from_cache:
                self.log("Storing output '%s' in '%s' from '%s'." % ( self.name,output_directory, nodename ) )
                self._cache['end_time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_cache(hash)
                queue.recv()

            # Reporting submit command
            if 'start_time' in self._cache:
                self.report("submission_%s_start" % hash, "submission/start/%s" % self.name, "text/plain", contents = self._cache['start_time'] )                

            if 'end_time' in self._cache:
                self.report("submission_%s_end" % hash, "submission/end/%s" % self.name, "text/plain", contents = self._cache['end_time'] )                

            self.report("submission_%s_submit" % hash, "submission/submit/%s" % self.name, "application/x-sh", contents = queue.command )                
            logfile = queue.log().val()
            self.report("submission_%s_log" % hash, "submission/log/%s" % self.name, "text/plain", contents = logfile )                

            # Storing the output for the reporter
            output_hash = queue.hash_output().val().strip()
            tmpfile = path.join(self.temporary_directory, "%s-%s.zip"%(self.name,output_hash))
            if not 'reporter_output_file_hash' in self._cache or not self._cache['reporter_output_file_hash'] == hash_filelist([tmpfile]):                
                pwd, dir = self._cache['output'].rsplit("/",1) # FIXME: Not windows compatible
                if dir.strip() == "":
                    pwd, dir = pwd.rsplit("/",1) # FIXME: Not windows compatible

                self.log("Generating (output) '%s' from '%s'." % ( tmpfile, dir ) )
                zipper(tmpfile, dir, pwd )
                self.workflow.register_temporary_file(tmpfile)
                filehash2 = hash_filelist([tmpfile])
            else:
                filehash2 = self._cache['reporter_output_file_hash']
                
            self.report("submission_%s" % output_hash, "submission/output/%s" % self.name, "application/zip", file = tmpfile)         

            # Updating the cache file
            self._cache.update({'output':output_directory,'output_hash': output_hash, 'reporter_input_file_hash':filehash1, 'reporter_output_file_hash':filehash2}) 
            self.save_cache(hash)

        return self._finished


class RawData(ProvenanceField):
    def __init__(self,output_directory, *args, **kwargs):
        super(RawData, self).__init__(*args, **kwargs)

        deps = self.dependencies
        if len(deps) != 1:
            raise BaseException("RawData can only depend on one Submission .")

        if not isinstance(deps[0], Submission):
            raise BaseException("RawData can only depend on Submission and not %s." %dep[0].__class__.__name__)        
       
        self._args = [a for a in args if not isinstance(a, Submission)]
        self._kwargs = dict([(a,b) for a,b in kwargs.iteritems() if not isinstance(b, Submission)])
        
        self._output = output_directory

    def execute(self, queue, *args, **kwargs):             
        self._computed = True
        return self._computed


    def finished(self):
        if not self._computed:
            self.execute(self._queue)

        d = {}
        i = 0
        for a in self._args:
            if callable(a):      
                d["arg%d"%i] = a(self.workflow, self.queue)
            else:
                d["arg%d"%i] = a
            i+=1
        for name, val in self._kwargs.iteritems():
            if callable(val):
                d[name] = val(self.workflow, self.queue)
            else:
                d[name] = val


        obj = self.dependencies[0]    
        self._value = Template(self._output).safe_substitute(d)
        self._finished = obj.finished(self._value)
        if not self._finished:
            self.log("Warning: could not create '%s' as computation '%s' has not finished yet." % (self.name, obj.name))      

        return self._finished

class Dependency(ProvenanceField):
    def __init__(self, name, *args, **kwargs):
        super(Dependency, self).__init__(*args, **kwargs)
        self._depends_on = name

    def execute(self, queue):
        self._value = self._depends_on
        self._computed = True
        return self._computed

    def finished(self):
        if not self._computed:
            self._finished = False
            self.execute(self._queue)
        return self._finished

class Treatment(ProvenanceField):
    def __init__(self, script_function, *args, **kwargs):
        super(Treatment, self).__init__(*args, **kwargs)

        self._function = script_function if callable(script_function) else None
        self._script = script_function if isinstance(script_function,str) else None        
        self._contents = ""
        self._mimetype = "unknown"
        if 'mimetype' in kwargs:
            self._mimetype = kwargs['mimetype']
        self._finished = False

    def execute(self, queue):
        self._computed = True
        fargs = ()
        sargs = ()
        for a in self.dependencies:
            if not a.finished():
                self.log("Warning: cannot perform treatment '%s' as '%s' is not finished." % (self.name, a.name))                 
                fargs  += (None,)
                sargs  += ("/tmp/",)
            else:
                fargs  += (a.value(),)
                sargs  += (format_path(a.value()),)

        if not self._function is None:
            self._value = self._function(self.workflow,*fargs)
            self._mimetype = "application/x-python"
            self._contents = inspect.getsource(self._function)
        elif not self._script is None:
            proc = subprocess.Popen("%s %s"%(self._script," ".join(sargs) ), shell=True, stdout=subprocess.PIPE)
            self._value,exitcode = proc.communicate()
            f = open(self._script)
            self._contents = f.read()
            f.close()
        self._finished =True
        return self._computed

    def finished(self):
        if not self._computed:
            self._finished = False
            self.execute(self._queue)

        return self._finished

    def value(self):
        if self.finished():
            node = self.nodename
            self.report("%s-input-%s" %(self.name, node), "treatment/input/%s"%self.name, self._mimetype, self._contents)
            self.report("%s-output-%s" %(self.name, node), "treatment/output/%s"%self.name, "text/plain", self._value)
            return self._value
        return None

        

class Reporter(ProvenanceField):

    appendix = [("machine/","label_machine%d", "Machine%d"), 
                ("depends/","label_depends%d", "Dependency details")]

    def __init__(self, output_directory, *args, **kwargs):
        super(Reporter, self).__init__(*args, **kwargs)
        self._base_url = "http://tobeimplemented/"
        self._item_order = []
        self._items = {}
        self._output_directory = output_directory
        self._downloads_directory = "downloads"
        self._output_directory_downloads = path.join(self._output_directory,self._downloads_directory)
        self._label_counter = 0
        self._current_label = None
        self._id_label = {}
        self._section_titles = {}
        self._section_short = {}

        self._body = ""
        self._firstlabel = None
        self._notecount = 0
        self._section_id = 0
        self._subsection_id = 0
        self._submission = 0
        self._occupied = []
        self._filecount = 0

    def occupy(self, server):
        self._occupied.append(server)

    def isoccupied(self,server):
        return server in self._occupied


    def get_url(self):
        return self._base_url

    def set_url(self, url):
        self._base_url = url

    base_url = property(get_url, set_url)

    @property
    def submission(self):
        return self._submission

    def increase_submission(self):
        self._submission +=  1

    def report(self,id, name, mimetype, contents = None, file = None):
        if "submission/input/" in name:
            self.increase_submission()
        self._item_order.append(id)
        self._items[id] = (name, mimetype,  contents,file)

#        print "REPORTING", (id, name, mimetype, system, contents,file, tmpfile)

    def attach_file(self, file, mimetype = "text/plain"):
        m = hashlib.new("md5")
        m.update(file)
        self.report("file_%s"%m.hexdigest(), "file/%d"%self._filecount, mimetype,file = file)
        self._filecount+=1


    def note(self, note):
        m = hashlib.new("md5")
        m.update(note)
        self.report("note_%s"%m.hexdigest(), "note/%d"%self._notecount, "text/plain",contents = note)
        self._notecount+=1

        return note

    def section_id(self):
        idd1 = "%d%s" % (self._section_id, chr(65+self._subsection_id))
        idd2 = "%d%s.%d" % (self._section_id, chr(65+self._subsection_id), self._submission )
        return idd1,idd2,self._current_label

    def __call__(self, section = None, subs = 0, label=None):
        if isinstance(section, str):
            if subs == 0:
                self._section_id += 1
                self._subsection_id = 0
            if subs == 1:
                self._subsection_id += 1

            m = hashlib.new("md5")
            m.update(section)
            id = "section_%s" % m.hexdigest()
            self.report(id, "section/%d"%subs, "text/plain", contents = section)
            ret = "\\"+"sub"*subs+"section{%s}\n" % section
            
            if isinstance(label,str):
                ret+="\\label{%s}\n" % label
                self._current_label = label
            else:

                self._current_label = "sub"*subs + "section%d"%self._label_counter
                self._label_counter+=1

            if self._firstlabel is None: self._firstlabel = self._current_label
            self._id_label.update({id: self._current_label})
            self._section_titles[self._current_label] = section
            self._section_short[self._current_label] = self.section_id()

            return ret

        self._submission = 0
        appendix_order = []
        appendix = {}

        # Render the main sections

        labelid = 1
        sectionid = 1
        used_ids = []
        for id in self._item_order:
            name, mimetype,  contents,file = self._items[id]
            skip = None
            for a,l,s in self.appendix:
                if a in name:
                    if not id in appendix_order:
                        appendix_order.append(id)
                        appendix[id] = {'name': name, 'label': l % labelid, 'labelid':labelid, 'text': s % labelid}
                        self._id_label[id] = appendix[id]['label']
                        self._section_titles[appendix[id]['label']] = appendix[id]['text']
                        labelid += 1
                    skip = True

            if not skip is None: 
                self._body+=self.refer_appendix(id=id, contents = appendix[id]['text'])
                continue


            name, mimetype, contents,file = self._items[id]                
            typ, _  = name.split("/",1)
            mimetype_parts = mimetype.split("/")
            block = ""
            fnc = None
            if id not in used_ids:
                if hasattr(self,"render_%s"%typ): fnc = getattr(self,"render_%s"%typ)
                elif fnc is None and hasattr(self,"render_%s"% "_".join(mimetype_parts)): fnc = getattr(self,"render_%s"% "_".join(mimetype_parts))
                elif fnc is None and hasattr(self,"render_%s"%mimetype_parts[0]): fnc = getattr(self,"render_%s"%mimetype_parts[0])
                else: fnc = getattr(self,"render")
                used_ids.append(id)
                if not id in self._id_label:
                    self._id_label[id] = self._current_label
            else:
                if hasattr(self,"refer_%s"%typ): fnc = getattr(self,"refer_%s"%typ)
                elif fnc is None and hasattr(self,"refer_%s"% "_".join(mimetype_parts)): fnc = getattr(self,"refer_%s"% "_".join(mimetype_parts))
                elif fnc is None and hasattr(self,"refer_%s"%mimetype_parts[0]): fnc = getattr(self,"refer_%s"%mimetype_parts[0])
                else: fnc = getattr(self,"refer")

            block = fnc(id, name, mimetype,contents,file)
            self._body += block

        # Render appendix
        for id in appendix_order:
            name, mimetype, contents,file = self._items[id]
            block = self.render_appendix(id,name,mimetype, contents,file)
            self._body += block
            
        if not os.path.exists(self._output_directory):
            os.makedirs(self._output_directory)
        f = open(path.join(self._output_directory,"index.html"),"w")

        f.write( self.finalize() )
        f.close()
        return ""

    def render_section(self,id=None, name=None, mimetype="text",contents=None,file=None):
        self._current_label = self._id_label[id]
        label = self._id_label[id]
        title = self._section_titles[label]
        print title
        print "="*len(title)
        print "label:"+label
        print 

    def refer(self,id=None, name=None, mimetype="text",contents=None,file=None):
        print "REFER TO:", self._id_label[id] , self._section_titles[self._id_label[id]]


    def render(self,id=None, name=None, mimetype="text",contents=None,file=None):
        if not contents is None:
            print "PT:", contents
            print "ID:", id
        else:
            print "DOWNLOAD:",file


    def render_text_plain(self,id=None, name=None, mimetype="text/plain",contents=None,file=None):
        if contents:
            print "PT:", contents
            print "ID:", id
        else:
            print "DOWNLOAD:",file

    def render_appendix(self,id=None, name=None, mimetype="text/plain",contents=None,file=None):
        label = self._id_label[id]
        self._current_label = label
        title = "Appendix: "+self._section_titles[label]
        print title
        print "="*len(title)
        print "label:"+label
        print
        if not contents is None:
            print contents
        
    def initialize(self):
        pass

    def finalize(self):
        return ""

class HtmlReporter(Reporter):

    appendix = [("machine/","label_machine%d", "Machine%d"), 
                ("depends/","label_depends%d", "Dependency details")]

    def __init__(self, output_directory, *args, **kwargs):
        super(HtmlReporter,self).__init__(output_directory, *args, **kwargs)
        self._toc = ""
        self._body = ""

    def supplementary(self, text="supplementary"):
        return r"\href{%s}{%s}" % (self._base_url, text )



    def finalize(self):
        html = """
<!DOCTYPE html>
<html>
<head>
  <link href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/themes/base/jquery-ui.css" rel="stylesheet" type="text/css"/>
  <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.5/jquery.min.js"></script>
  <script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/jquery-ui.min.js"></script>
<style>
${style}
</style>  
  <script>
  var tabs;
  $(document).ready(function() {
    tabs = $("#tabs").tabs();
    $(".clickable").click(function() {
 $(tabs).tabs('select', $(this).attr("href") );
});
  });
  </script>
</head>
<body style="font-size:62.5%;">
  
<div id="tabs">
    <ul>
${toc}
    </ul>
    <div style="display:none;">
${tabs}
    </div>
</div>
</body>
</html>

"""
        first = self._firstlabel
        if self._firstlabel is None: first = ""
        return html.replace("${toc}", self._toc)\
            .replace("${tabs}", self._body)\
            .replace("${label}",first)\
            .replace("${style}",  HtmlFormatter().get_style_defs('.highlight'))
        
    def render_note(self,id=None, name=None, mimetype="text",contents=None,file=None):
        
        return "<p>"+contents+"</p>"


    def render_section(self,id=None, name=None, mimetype="text",contents=None,file=None):
        html1 = "<li><a href=\"#${label}\"><span>${short}. ${title}</span></li>"
        html2 = "</div><div id=\"${label}\"><h2>${short}. ${title}</h2>"

        self._current_label = self._id_label[id]
        label = self._id_label[id]
        title = self._section_titles[label]
        short,_,_ = self._section_short[label]

        self._toc += Template(html1).safe_substitute({'title': title, 'label': label, 'short': short})
        
        return Template(html2).safe_substitute({'title': title, 'label': label, 'short': short})

    def refer(self,id=None, name=None, mimetype="text",contents=None,file=None):
        html1 = """<a href="#${label}" class="clickable">${title}</a>""" 
        ret = Template(html1).safe_substitute({'label': self._id_label[id], 'title': self._section_titles[self._id_label[id]]})
        return ret

    def refer_appendix(self,id=None, name=None, mimetype="text",contents=None,file=None):        
        self.increase_submission()
        html1 = "<h4>%d. Submission</h4>" % self.submission
        html1 += """<p><strong>Machine:</strong> ${title} - see <a href="#${label}" class="clickable">Appendix: ${title}</a> for details.</p>""" 
        ret = Template(html1).safe_substitute({'label': self._id_label[id], 'title': self._section_titles[self._id_label[id]]})
        return ret


    def refer_submission(self,id=None, name=None, mimetype="text",contents=None,file=None):
        _, inout, codeid = name.split("/",2)
        block = ""
        if inout == "input":
            block ="<p><strong>Source code (%s)</strong>: see %s</p>" % (codeid,self.refer(id, name, mimetype,contents,file) )
        elif inout == "submit":
            block ="<p>Using the raw data from earlier (%s in %s) we proceeded:" % (codeid,self.refer(id, name, mimetype,contents,file) )

        return block


    def render(self,id=None, name=None, mimetype="text/plain",contents=None,file=None, filename ="unknown"):
        html1 = """<p>${contents}</p>"""
        html2 = """<p><strong>Filename:</strong> ${filename}<br /><br />${contents}</p>"""
        html3 = """<a href="${file}">""" + filename + "</a>"
        if not contents is None:
            contents = str(contents)
            try:
                lexer = get_lexer_for_mimetype(mimetype)
            except: 
                lexer = None
            if lexer:
                contents = highlight(contents, lexer, HtmlFormatter())
            return Template(html1).safe_substitute({'contents': contents})
        else:
            contents = None
            lexer = None
            try:
                if not lexer :
                    lexer = get_lexer_for_mimetype(mimetype)
            except:
                pass
            try:
                if not lexer :
                    lexer = guess_lexer_for_filename(file)
            except:
                pass

            if lexer:
                f = open(file, "r")
                contents = f.read()
                f.close()
                contents = highlight(contents, lexer, HtmlFormatter())
                return Template(html2).safe_substitute({'contents': contents, 'filename': file})                

            _, filename = file.rsplit("/",1)
            urlfile = "%s/%s" % (self._downloads_directory,filename)
            if not os.path.exists(self._output_directory_downloads):
                os.makedirs(self._output_directory_downloads)
            newfile = path.join(self._output_directory_downloads, filename)
            self.log("Copying '%s' to '%s'." % ( file, newfile ))
            shutil.copy(file, newfile)
            return Template(html3).safe_substitute({'file': urlfile})

    def render_submission(self,id=None, name=None, mimetype="text/plain",contents=None,file=None):
        _, inout, codeid = name.split("/",2)
        block = ""
        if inout == "start":
            block += "<p><strong>Submitted</strong>: %s.</p>"  % contents
        elif inout == "end":
            block += "<p><strong>Data pulled</strong>: %s.</p>"  % contents
        elif inout == "input":
            block += "<p><strong>Source code (referred to as <span class=\"keyword\">%s</span>)</strong> %s.</p>"  % (codeid,self.render(id, name, mimetype,contents,file, filename="Download"))

        elif inout == "output":
            block = "<p><strong>Output files</strong>:The raw data from the simulation can be downloaded %s.</p>"  % self.render(id, name, mimetype,contents,file, filename="here")

        elif inout == "submit":
            block ="<p>The code was executed by submitting following command(s):"
            block+=self.render(id, name, mimetype,contents,file)
        elif inout == "log":
            if contents.strip() != "":
                block ="<p>The log of the submission is:</p>" 
                block+=self.render(id, name, mimetype,contents,file)
            else:
                block ="<p>The submission produces no output to stdout and stderr.</p>" 
        return block

    def render_treatment(self,id=None, name=None, mimetype="text/plain",contents=None,file=None):
        _, inout, codeid = name.split("/",2 )
        block = ""        
        if inout == "input":
            block = "<p>We applied the following procedure:</p>"
            block += self.render(id, name, mimetype,contents,file)
        elif inout == "output":
            block = "<p>to get:</p>"
            block += self.render(id, name, mimetype,contents,file)
        return block

    def render_text_plain(self,id=None, name=None, mimetype="text/plain",contents=None,file=None):
        return self.render(id, name, mimetype,contents,file)

    def render_appendix(self,id=None, name=None, mimetype="text/plain",contents=None,file=None):
        html1 = "<li><a href=\"#${label}\"><span>Appendix: ${title}</span></a></li>"
        html2 = "</div><div id=\"${label}\"><h2>${title}</h2>${contents}"

        self._current_label = self._id_label[id]
        label = self._id_label[id]
        title = self._section_titles[label]

        self._toc += Template(html1).safe_substitute({'title': title, 'label': label})
        
        contents = self.render(id, name, mimetype,contents,file)
        return Template(html2).safe_substitute({'title': title, 'label': label,'contents': contents})


class MetaWorkflow(type):
    def __new__(cls, name, bases, dct):
        fields = []

        # Inherithed fields
        for b in bases:
            if hasattr(b, "__new_fields__"):
                fields += [(x,y,) for x,y in b.__new_fields__.iteritems()]
        fields = dict(fields)

        # Finding new fields
        newfields = [(a,dct[a]) for a in dct.iterkeys() if isinstance(dct[a], ProvenanceField) or isinstance(dct[a], Reporter)]
        fields.update(newfields)

        # TODO: Currently there is no mechanism for handling overwritten fields
                
        dct['__new_fields__'] = fields

        return type.__new__(cls, name, bases, dct)
 

class Workflow(object):
    __metaclass__ = MetaWorkflow
    def log(self, msg):
        print msg

    def add_reporter(self,reporter):
        self._reporters.append(reporter)
        for name, attr in self._items:    
            attr.register_reporter(reporter)    

    def __init__(self, queue, *args,**kwargs):
        self.fields = copy.deepcopy(self.__class__.__new_fields__)        
        self._dependencies = []
        self._base_url = "http://localhost/"
        items = [(a,b) for a,b in self.fields.iteritems()]
        items.sort(lambda (a,x),(b,y): cmp(x.__counter__, y.__counter__))
        self._queue = queue
        reporters = [b for a,b in items if isinstance(b, Reporter)]
#        print "REPOR",reporters
        self._reporters = reporters
        tmp = tempfile.mkdtemp()
        self._items = items
        for name, attr in items: 
            setattr(self, name, attr)
            attr.queue = queue
            attr.name = name
            attr.workflow = self
            attr.temporary_directory = tmp
            attr.register_reporters(reporters)
            attr.base_url = self._base_url
#            self.pwd_directory = 
        self._tmpfiles = []




    def get_url(self):
        return self._base_url

    def set_url(self, url):
        self._base_url = url
        for name, attr in self._items:
            attr.base_url = self._base_url
        for  attr in self._reporters:
            attr.base_url = self._base_url


    base_url = property(get_url, set_url)

    def register_temporary_file(self,file):
        self._tmpfiles.append(file)

    def clean(self):
        for file in self._tmpfiles:
            self.log("Deleting %s." % file)
            os.remove(file)

#    zipper("/Users/tfr/TestIn.zip","TestInDir/","/Users/tfr/")
#  or chatr
# ldd
# otool -L _build/omp_ising_GeneratorSSE
#
# Notes:
# Compile with -MD
