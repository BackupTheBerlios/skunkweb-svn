import zipfile
import time
import os 
from skunk.vfs.vfs import FS, VFSException, FileNotFoundException, NotWriteableException
from skunk.vfs.readOnlyStream import ReadOnlyStream
from skunk.vfs.pathutil import Archive, adjust_user_path

class ZipFS(FS):
    writeable=False
    
    def __init__(self, zippath, root='', prefix='/'):
        if not zipfile.is_zipfile(zippath):
            raise zipfile.BadZipfile, "not a zip file: %s" % zippath
        self.zpath=os.path.abspath(zippath)
        self._zfile=zipfile.ZipFile(zippath, mode='r')
        self._archive=Archive(root, prefix)
        self.prefix=prefix
        self.root=root
        self._archive.savePaths(self._zfile.namelist())

    def vstat(self, path):
        adjusted=adjust_user_path(path)
        if not self._archive.paths.has_key(adjusted): 
            raise FileNotFoundException, path
        realname=self._archive.paths[adjusted]
        if realname==None:
            arcstat=os.stat(self.zpath)[7:]
            return (0,) + arcstat
        info=self._zfile.getinfo(realname)
        modtime=int(time.mktime(info.date_time + (0, 0, 0)))
        return info.file_size, -1, modtime, modtime

    def open(self, path, mode='r'):
        adjusted=adjust_user_path(path)
        if mode!='r':
            raise NotWriteableException, "unsupported file open mode: %s" % mode
        if not self._archive.paths.has_key(adjusted):
            raise FileNotFoundException, path
        realname=self._archive.paths[adjusted]
        if realname!=None:
            return ReadOnlyStream(adjusted,
                                  self._zfile.read(realname))
        else:
            raise VFSException, "cannot open directory as file: %s" % path

    def listdir(self, path):
        if not self.isdir(path):
            raise VFSException, "not a directory: %s" % path
        return self._archive.listdir(path)
        
    def exists(self, path):
        return self._archive.exists(path)

    def isdir(self, path):
        adjusted=adjust_user_path(path)
        if not self._archive.paths.has_key(adjusted):
            return 0
        realname=self._archive.paths[adjusted]
        if realname==None:
            return 1
        else:
            # on UNIX, I'd hope to get this from file attributes;
            # Per Boethner's implementation of java.util.zip.ZipEntry
            # for GNU Classpath only tests the final slash
            return realname.endswith('/') and \
                   self._zfile.getinfo(realname).file_size==0

    def isfile(self, path):
        adjusted=adjust_user_path(path)
        if not self._archive.paths.has_key(adjusted):
            return 0
        realname=self._archive.paths[adjusted]
        if realname==None:
            return 0
        else:
            return not adjusted.endswith('/')

__all__=['ZipFS']
