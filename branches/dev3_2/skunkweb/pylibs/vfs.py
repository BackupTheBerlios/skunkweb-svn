# $Id: vfs.py,v 1.1.2.1 2001/09/19 05:24:58 smulloni Exp $
# Time-stamp: <01/09/19 01:21:56 smulloni>

########################################################################
#  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
########################################################################

import exceptions
import os
import stat

# constants for "ministat"
MST_SIZE=0
MST_ATIME=1
MST_MTIME=2
MST_CTIME=3

class VFSException(exceptions.Exception): pass

def move(fs, path, newpath, newfs=None):
    if not newfs:
        fs.rename(path, newpath)
    else:
        if not fs.exists(path):
            raise VFSException, "no such file or directory: %s" % path
        if fs.isdir(path):
            _movedir(fs, path, newpath, newfs)
        else:
            _movefile(fs, path, newpath, newfs)

def _movedir(fs, path, newpath, newfs):
    def walker(arg, d, files, path=path, newpath=newpath, fs=fs, newfs=newfs):
        targetDir=os.path.join(newpath, d[len(path):])
        if newfs.exists(targetDir) and not newfs.isdir(targetDir):
            raise VFSException, "file %s already exists" % targetDir
        newfs.mkdir(targetDir)
        for f in files:
            _movefile(fs, os.join(d, file), os.join(targetDir, file), newfs)
    fs.walk(path, walker, 0)            

def _movefile(fs, path, newpath, newfs):
    try:
        f=fs.open(path)
        n=newfs.open(newpath, 'w')
        for l in f.xreadlines():
            n.write(l)
        f.close()
        n.close()
        fs.remove(path)
    except:
        e=sys.exc_info()[0]
        if newfs.exists(newpath):
            try:
                newfs.remove(newpath)
            except: pass
        raise e
                        

class FS:
    """
    abstraction layer (common file model) for file systems, with those features
    needed by SkunkWeb in particular.
    """

    def ministat(self, path):
        raise NotImplementedError

    def mkdir(self, dir):
        raise NotImplementedError

    def mkdirs(self, dir):
        raise NotImplementedError
    
    def rmdir(self, dir):
        raise NotImplementedError
    
    def open(self, path, mode='r'):
        """
        returns a file object
        """
        raise NotImplementedError
    
    def listdir(self, dir):
        raise NotImplementedError

    def walk(self, dir, visitfunc, arg):
        try:
            names = self.listdir(dir)
        except:
            return
        visitfunc(arg, dir, names)
        for name in names:
            name = os.path.join(top, name)
            if self.exists(name) and self.isdir(name):
                self.walk(name, func, arg)
            
    def rename(self, path, newpath):
        raise NotImplementedError
    
    def exists(self, path):
        try:
            self.ministat(path)
            return 1
        except:
            return 0
    
    def isdir(self, path):
        raise NotImplementedError

    def isfile(self, path):
        raise NotImplementedError
    
    def getatime(self,path):
        st=self.ministat(path)
        return st[MST_ATIME]
    
    def getmtime(self, path):
        st=self.ministat(path)
        return st[MST_MTIME]

    def getctime(self, path):
        st=self.ministat(path)
        return st[MST_CTIME]
    
    def getsize(self, path):
        st=self.ministat(path)
        return st[MST_SIZE]
    
    def getproperty(self, path, property):
        raise NotImplementedError

    def setproperty(self, path, property, value):
        raise NotImplementedError
    

class LocalFS(FS):

    def ministat(self, path):
        try:
            return os.stat(path)[6:10]
        except os.error, oyVeh:
            raise VFSException, "[Errno %d] %s: %s" % (oyVeh.errno,
                                                       oyVeh.strerror,
                                                       oyVeh.filename)
    def mkdir(self, dir):
        os.mkdir(dir)

    def mkdirs(self, dir):
        os.makedirs(dir)
    
    def rmdir(self, dir):
        os.rmdir(dir)
    
    def open(self, path, mode='r'):
        """
        returns a file object, corresponding to the builtin function open, not to os.open
        """
        return open(path, mode)
    
    def listdir(self, dir):
        return os.listdir(dir)

    def rename(self, path, newpath):
        os.rename(path, newpath)
    
    def isdir(self, path):
        return os.path.isdir(path)

    def isfile(self, path):
        return os.path.isfile(path)

########################################################################
# $Log: vfs.py,v $
# Revision 1.1.2.1  2001/09/19 05:24:58  smulloni
# adding vfs
#
########################################################################
