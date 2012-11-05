from batchq.pipelines.shell.bash import BashTerminal
from batchq.pipelines.shell.ssh import SSHTerminal
from batchq.pipelines.shell.sftp import SFTPTerminal
import time
class FileTransferTerminal(SFTPTerminal):
    """
    This object is similar to SFTPTerminal if server, username and
    password are passed to the constructor. If server=None, this class
    implements the SFTPTerminal operations for the for local file
    system. Wether a FileTransferTerminal class is working on the local
    filesystem or not can be checked with FileTransferTerminal.islocal().
    """

    def __init__(self, server = None, username = "", password = "", port = 22, accept_figerprint = False):
        self._server = server
        if not server is None:
            super(FileTransferTerminal,self).__init__(server, username, password, port, accept_figerprint)
        else:
            self._remote_dir = os.getcwd()            
            self._local_dir = os.getcwd()            

    def islocal(self):
        if self._server is None:
            return True
        return False

    def chdir(self, path):        
        if self._server:
            return super(FileTransferTerminal,self).chdir(path)
        else:
            if os.path.isdir(path):
                self._remote_dir = path
                return True
        return False

    def local_chdir(self, path):
        if self._server:
            return super(FileTransferTerminal,self).local_chdir(path)
        else:
            if os.path.isdir(path):
                self._local_dir = path
                return True
        return False

    def pwd(self):
        if self._server:
            return super(FileTransferTerminal,self).pwd()
        else:
            return self._remote_dir

    def local_pwd(self):
        if self._server:
            return super(FileTransferTerminal,self).local_pwd()
        else:
            return self._local_dir

    def _copy(self, file1, file2):
        """
        This function does not use shutil as shutil does not handle
        whitespaces correctly.
        """
        # FIXME: Not wwindows compatiable
        os.system ("cp '%s' '%s'" % (file1, file2))
        return os.path.isfile(file2)

    def sendfile(self, local_file, remote_file):
        if self._server:
            return super(FileTransferTerminal,self).sendfile(local_file, remote_file)
        else:
            return self._copy(os.path.join(self._local_dir,local_file),os.path.join(self._remote_dir,remote_file))

    def getfile(self, local_file, remote_file):
        if self._server:
            return super(FileTransferTerminal,self).getfile(local_file, remote_file)
        else:
            return self._copy(os.path.join(self._remote_dir,remote_file),os.path.join(self._local_dir,local_file))


class FileCommander(FileTransferTerminal):
    """
    FileCommander provides an easy-to-use interface for transfering 
    files as well as access both the local and the remote file system. It 
    performs common operations such compare directories in the local and
    remote views as well as syncronising them.

    The local and remote terminals can be access through the property
    FileCommander.local and FileCommander.remote, respectively, which
    are both instances of the BashTerminal.
    """

    MODE_LOCAL_REMOTE = 1
    MODE_REMOTE_LOCAL = 2

    def __init__(self, server = None, username = "", password = "", port = 22, login_expect = None, accept_figerprint = False):
        super(FileCommander,self).__init__(server, username, password, port, accept_figerprint)

        self._local_bash = BashTerminal()
        self._syncroisation_cache = {}
        if server:
            self._remote_bash = SSHTerminal(server, username, password, port, accept_figerprint, login_expect = login_expect) 
        else:
            self._remote_bash = BashTerminal()

    @property
    def local(self):
        """
        This property returns an instance of ``BashTerminal``.
        """
        return self._local_bash

    @property
    def remote(self):
        """
        This property returns an instance of ``SSHTerminal`` connected
        to the remote machine if server was different than ``None`` in
        the constructor. Otherwise, an instance of ``BashTerminal`` is returned.
        """
        return self._remote_bash


    def diff(self, local_dir = ".", remote_dir =".", recursive = True, mode = 3, absolute_path = False, ignore_hidden =True):
        """
        Compare local and remote directories, recursively ``recursive =
        True`` (default),  by computing a hash of each file.  
        Depending on wether ``mode`` is set to
        ``FileCommander.MODE_LOCAL_REMOTE`` or ``FileCommander.MODE_REMOTE_LOCAL``  
        two lists are returned with files and directories that are
        out-of-date, or missing. As standard, hidden files are
        ignored. To include hidden files  set ``ignore_hidden =
        False``. By default, paths returned are relative, but if
        ``absolute_path = True`` they are converted into absolute paths.
        """

        if not self.local.pushd(local_dir):
            raise BaseException("Local directory does not exist")
        if not self.remote.pushd(remote_dir):
            raise BaseException("Remote directory does not exist")

        lpwd = self.local.pwd()
        rpwd = self.remote.pwd()

        format_lpath = lambda x: x if not absolute_path else self.local.path.join(lpwd,x)
        format_rpath = lambda x: x if not absolute_path else self.remote.path.join(rpwd,x)
       

        (lfiles, ldirs) = self.local.list(".", recursive,list_files = False)
        (rfiles, rdirs) = self.remote.list(".", recursive,list_files = False)

        lfiles_sum  = self.local.sum_files(".",ignore_hidden)

        rfiles_sum  = self.remote.sum_files(".",ignore_hidden)        

        files = []
        dirs = []
        already_checked = []


        if mode & 1:
            for file,sum in lfiles_sum:
                already_checked += [file,]
                if not (file,sum) in rfiles_sum:
                    files+= [(format_lpath(file), "")]

        if mode & 2:
            for file,sum in rfiles_sum:
                already_checked += [file,]
                if not (file,sum) in lfiles_sum:
                    files+= [("", format_rpath(file))]
       
        already_checked = []
        
        if mode & 1:
            for dir in ldirs:
                if (dir[0] == "." or "/." in dir) and ignore_hidden: continue
                already_checked += [dir,]
                if not dir in rdirs:
                    dirs += [(format_lpath(dir), "")]

        if mode & 2:
            for dir in rdirs:
                if (dir[0] == "." or "/." in dir) and ignore_hidden: continue
                if dir in already_checked: continue
                if not dir in ldirs:
                    dirs += [("", format_lpath(dir))]


        if not self.local.popd():
            raise BaseException("Local direcory stack error")
        if not self.remote.popd():
            raise BaseException("Remote direcory stack error")


        return (files, dirs)


    def sync(self, local_dir = ".", remote_dir =".", recursive = True, mode = 3, ignore_hidden =True, diff_local_dir =None, diff_remote_dir =None, use_tar = False):
        """
        This function compares a local and a remote directory and
        transfer missing files in one direction depending on the mode
        (which can either be ``FileCommander.MODE_LOCAL_REMOTE`` or
        ``FileCommander.MODE_REMOTE_LOCAL``). Note this function ignores the
        creation/modification date of the file or directory.
        """

        oldlocal = self.local_pwd()
        oldremote = self.pwd()

        if not self.local_chdir(local_dir): 
            return None
        if not self.chdir(remote_dir): 
            return None
        if diff_local_dir is None: diff_local_dir = local_dir
        if diff_remote_dir is None: diff_remote_dir = remote_dir

        if mode == self.MODE_LOCAL_REMOTE:
            lfiles, ldirs = self.diff(diff_local_dir, diff_remote_dir, recursive, self.MODE_LOCAL_REMOTE, False, ignore_hidden)            
            copyfnc = self.sendfile
            bash = self.remote
            other_bash = self.local
            files =[file for file,_ in lfiles]
            dirs =[dir for dir,_ in ldirs]
            work_dir = remote_dir
        elif mode == self.MODE_REMOTE_LOCAL:
            rfiles, rdirs = self.diff(diff_local_dir, diff_remote_dir, recursive, self.MODE_REMOTE_LOCAL, False, ignore_hidden)
            copyfnc = self.getfile
            bash = self.local
            other_bash = self.remote
            files = [file for _,file in rfiles]
            dirs = [dir for _,dir in rdirs]
            work_dir = local_dir
        else:
            raise BaseException("Select one and only one mode.")

        if not bash.pushd(work_dir):
            raise BaseException("Directory does not exist %s" %work_dir)

        # Syncronising directories
        for dir in sorted(dirs):
            if dir.strip() == "":
                raise BaseException("Error recieved an empty directory")
            if not bash.mkdir(dir):
                raise BaseException("Could not create: '%s'. Issued '%s' and got following output: '%s'" % (dir, bash.last_input,bash.last_output))

        # Syncronising files
        if use_tar and len(files) > 0:
            i = 1
            filename = ".syncronisation_%d.tar" %i
            while other_bash.isfile(filename) or bash.isfile(filename):
                i += 1
                filename = ".syncronisation_%d.tar" %i

            if not other_bash.create_tar(filename, files):
                raise BaseException("Could not create tar archive: '%s' and '%s'" % (file, other_bash.last_input,other_bash.last_output))

            if not copyfnc(filename,filename):
                raise BaseException("Could not transfer tar archive: '%s' and '%s'" % (str(self.last_input),str(self.last_output)))
            other_bash.rm(filename)


            while not bash.isfile(filename):
                time.sleep(1)

            if not bash.extract_tar(filename):
                raise BaseException("Could not extract tar archive: '%s' and '%s'" % (str(bash.last_input),str(bash.last_output)))
            bash.rm(filename)

        if not use_tar:
            for file in sorted(files):
                if file.strip() == "":
                    raise BaseException("Error recieved an empty directory.")
                if not copyfnc(file,file):
                    raise BaseException("Could not copy: '%s'. Issued '%s' and got following output: '%s'" % (file, self.last_input,self.last_output))

        if not bash.popd():
            raise BaseException("Could not pop working directory.")

        self.local_chdir(oldlocal)
        self.chdir(oldremote)


        if len(dirs) == 0 and  len(files) == 0:
            return False

        return (dirs, files)
