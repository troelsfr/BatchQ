####################################################################################
# Copyright (C) 2011-2012
# Troels F. Roennow, ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
####################################################################################

import os
import hashlib
import re
from batchq.core.errors import HashException
import zipfile

cmdhasher = "md5"
hasher_routine = "md5"

def zipper(filename, relative_path, pwd = None):
    orgp = os.getcwd()
    if not pwd is None:  os.chdir(pwd)
    zfile = zipfile.ZipFile(filename, 'w')

    def add(p): 
        if os.path.isfile(p):
            zfile.write(p)
            return 

        for file in os.listdir(p):
            add( os.path.join(p, file) )

    add(relative_path)
    zfile.close()
    os.chdir(orgp)



def which (filename, lookin = [], env = None):
    if os.path.dirname(filename) != '':
        if os.access (filename, os.X_OK):
            return filename

    if env is None:
        env = os.environ

    lookin = lookin + env['PATH'].split(os.pathsep) if 'PATH' in env else lookin
    lookin.append(os.defpath)

    for path in lookin:
        f = os.path.join(path, filename)
        if os.access(f, os.X_OK):
            return f
    return None


def filelist(path, list = None):        
    """
    Computes the a file list of the given path.
    """
    if list is None:
        list = []
    for filename in sorted(os.listdir(path)):      
        newpath = os.path.join(path, filename) 

        if os.path.isfile(newpath):
            list +=[newpath]
        else:
            list = filelist(newpath, list) 
    return list

def hash_filelist(list):
    """
    Computes the hash of a filelist. 
    """
    global hasher_routine
    haobj = hashlib.new(hasher_routine)
    for filename in list:
        if os.path.isfile(filename):
            f = file(filename ,'rb') 
            haobj.update(f.read())
            f.close()
    hex =haobj.hexdigest()

    return hex

def directory_hash(dir):
    """
    Computes the hash of a filelist. 
    """
    if not os.path.isdir(dir):
        raise HashException("'%s' is not a directory." % dir)

    return hash_filelist(sorted(filelist(dir)))

def file_hash(file):
    """
    Computes the hash of a file. 
    """
    if not os.path.isfile(file):
        raise HashException("'%s' is not a file." % file)
    return hash_filelist([file])

def hash(path):
    if os.path.isfile(path):
        return file_hash(path)
    if os.path.isdir(path):
        return directory_hash(path)

    raise HashException("File or directory does not exist.")

def bash_hash_directory(dir):
    """
    Gives the equivalent bash command to directory_hash(dir).
    """
    print "DEPRECATED !!!!!!"
    global cmdhasher
#    return "find '%s' -type f -print0 | sort -z" % (dir)
    return "find '%s' -type f -print0 | sort -z | xargs -0 cat | %s" % (dir, cmdhasher)

def bash_hash_file(file):
    """
    Gives the equivalent bash command to file_hash(dir).
    """
    print "DEPRECATED !!!!!!"
    global cmdhasher
    return "%s '%s'" % (cmdhasher, file)

def bash_hash_pattern():
    print "DEPRECATED !!!!!!"
    return r"(?P<hash>[a-fA-F\d]{32})"

def bash_extract_hash(response):
    print "DEPRECATED !!!!!!"
#    return response
    searcher_for = re.compile(bash_hash_pattern())
    match = searcher_for.search(response)
    if not match:
        raise HashException("The output '%s' did not contain a hash string of the expected format."%response)

    return match.group("hash")

