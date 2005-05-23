import exceptions
import re
import shutil
import os
from os.path import (dirname, 
                     normpath, 
                     join as pathjoin, 
                     split as pathsplit)

from skunk.vfs.pathutil import containedPaths

# constants for "vstat"
VST_SIZE=0
VST_ATIME=1
VST_MTIME=2
VST_CTIME=3

VFSRegistry={}

_keyRE=re.compile(r'.*(\d+)$')

def registerFS(fs, key='default'):
    for k, f in VFSRegistry.items():
        if fs is f:
            return k
    while key in VFSRegistry.keys():
        m=_keyRE.search(key)
        if not m:
            d=1
        else:
            # I dare you to overflow this int
            d=int(m.group(1))+1
        key='%s%d' % (key, d)
    VFSRegistry[key]=fs
    return key

class VFSException(exceptions.Exception):
    pass

class FileNotFoundException(VFSException):
    pass

class NotWriteableException(VFSException):
    pass

def move(fs, path, newpath, newfs=None):
    if not newfs:
        fs.rename(path, newpath)
    else:
        if not fs.exists(path):
            raise FileNotFoundException, path
        if fs.isdir(path):
            _movedir(fs, path, newpath, newfs)
        else:
            _movefile(fs, path, newpath, newfs)

def _movedir(fs, path, newpath, newfs):
    def walker(arg,
               d,
               files,
               path=path,
               newpath=newpath,
               fs=fs,
               newfs=newfs):
        targetDir=pathjoin(newpath, d[len(path):])
        if newfs.exists(targetDir) and not newfs.isdir(targetDir):
            raise VFSException, "file %s already exists" % targetDir
        newfs.mkdir(targetDir)
        for f in files:
            _movefile(fs,
                      pathjoin(d, file),
                      pathjoin(targetDir, file), newfs)
    fs.walk(path, walker, 0)            

def _movefile(fs, path, newpath, newfs):
    try:
        f=fs.open(path)
        n=newfs.open(newpath, 'w')
        for l in f:
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



class FS(object):
    """
    abstraction layer (common file model) for file systems.
    """
    def isWriteable(self):
        """
        returns whether the fs supports write operations;
        says nothing about whether a write is permitted
        for a particular path
        """
        
        if hasattr(self.__class__, 'writeable'):
            return self.__class__.writeable
        else:
            return None

    def vstat(self, path):
        raise NotImplementedError

    def mkdir(self, dir):
        raise NotImplementedError

    def mkdirs(self, dir):
        raise NotImplementedError
    
    def remove(self, path):
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
            name = pathjoin(dir, name)
            if self.exists(name) and self.isdir(name):
                self.walk(name, visitfunc, arg)

    def find_path(self, dname, base, root='/'):
        """
        searches upwards from directory dname to directory root for a file called base.
        If found, the full path of the found file is returned; otherwise returns None.
        """

        while 1:
            if not dname.startswith(root):
                return 
            try:
                p=pathjoin(dname, base)
                self.vstat(p)
            except FileNotFoundException: 
                if dname==root:
                    return
                dname=dirname(dname)
            else: 
                return p

    def rename(self, path, newpath):
        raise NotImplementedError

    def copy(self, path, newpath):
        raise NotImplementedError
    
    def exists(self, path):
        try:
            self.vstat(path)
            return 1
        except:
            return 0

    def split_extra(self, path, extra_info='', nodir=1):
        """
        if given a path will extra path info, will
        return (path of existing file, extra path info)
        if some part of the path represents an existing file, and
        ('', '') if there is no file.  If nodir is true,
        the file must not be a directory unless extra_info=='', or
        the return value will be ('', '').
        """
        
        if path=='':
            return ('', '')
        if self.exists(path):
            if nodir and self.isdir(path) and extra_info!='':
                return ('', '')
            return path, extra_info
        else:
            p, e=pathsplit(path)
            if extra_info:
                ex='%s/%s' % (e, extra_info)
            else:
                ex=e
            return self.split_extra(p, ex, nodir)
    
    def isdir(self, path):
        raise NotImplementedError

    def isfile(self, path):
        raise NotImplementedError
    
    def getatime(self,path):
        st=self.vstat(path)
        return st[VST_ATIME]
    
    def getmtime(self, path):
        st=self.vstat(path)
        return st[VST_MTIME]

    def getctime(self, path):
        st=self.vstat(path)
        return st[VST_CTIME]
    
    def getsize(self, path):
        st=self.vstat(path)
        return st[VST_SIZE]

    
class LocalFS(FS):

    writeable=1

    def __init__(self, root='/', followSymlinks=1):
        self.root=normpath(root)
        self.followSymlinks=followSymlinks

    def _resolvepath(self, path):
        norm=normpath('%s/%s' % (self.root, path))
        if norm < self.root:
            raise FileNotFoundException, path
        return norm

    def vstat(self, path):
        realpath=self._resolvepath(path)
        try:
            if self.followSymlinks:
                return os.stat(realpath)[6:10]
            else:
                return os.lstat(realpath)[6:10]
        except os.error, oyVeh:
            if oyVeh.errno==2:
                raise FileNotFoundException, path
            raise VFSException, "[Errno %d] %s: %s" % (oyVeh.errno,
                                                       oyVeh.strerror,
                                                       oyVeh.filename)
    def mkdir(self, dir):
        os.mkdir(self._resolvepath(dir))

    def mkdirs(self, dir):
        os.makedirs(self._resolvepath(dir))
    
    def remove(self, path):
        realpath=self._resolvepath(path)
        if self.isdir(realpath):
            shutil.rmtree(realpath)
        else:
            os.remove(realpath)
    
    def open(self, path, mode='r'):
        """
        returns a file object, corresponding to the builtin function open, not to os.open
        """
        return open(self._resolvepath(path), mode)
    
    def listdir(self, dir):
        return os.listdir(self._resolvepath(dir))

    def copy(self, path, newpath):
        # based on shutil.copytree, but always copies symlinks, and doesn't
        # catch exceptions
        realpath=self._resolvepath(path)
        realnew=self._resolvepath(newpath)
        if self.isdir(realpath):
            names = os.listdir(realpath)
            os.mkdir(realnew)
            for name in names:
                srcname = pathjoin(realpath, name)
                dstname = pathjoin(realnew, name)
                if os.path.islink(srcname):
                    linkto = os.readlink(srcname)
                    os.symlink(linkto, dstname)
                elif os.path.isdir(srcname):
                    self.copy(srcname, dstname)
                else:
                    shutil.copy2(srcname, dstname)        
        else:
            shutil.copy(realpath, realnew)

    def rename(self, path, newpath):
        os.rename(self._resolvepath(path), self._resolvepath(newpath))
    
    def isdir(self, path):
        return os.path.isdir(self._resolvepath(path))

    def isfile(self, path):
        return os.path.isfile(self._resolvepath(path))

frontslashRE=re.compile(r'^/')
endslashRE=re.compile(r'/$')

class MultiFS(FS):
    """
    
    an FS implementation that permits other FS's to be
    mounted within it
    """
    def __init__(self,  mountdict=None):

        """
        mountdict should be a dict of the form:
        
        {'/desired/mount/point/' : [FSImplementation(),
                                    FSImplementation(), ...],
        ... }
        
        i.e., the keys are mount points, and the values are lists of
        fs implementations.  See MultiFS.mount, below.  The mount
        points can either be strings or other objects which return a
        mount point via their __str__ method; this enables the mount
        point to be determined dynamically.

        """
        if mountdict!=None:
            self.mounts=mountdict
        else:
            self.mounts={}
        self._mountpoints=self.mounts.keys()
        self._sortMountPoints()

    def _sortMountPoints(self):
        """
        keeps mount points sorted longest first (and otherwise in
        alphabetical order, which doesn't actually matter)
        """
        def lencmp(x, y):
            xs, ys=map(str, (x, y))
            return cmp(len(ys), len(xs)) or cmp(xs, ys)
        self._mountpoints.sort(lencmp)
        
    def mount(self, fs, mountPoint='/'):
        if self.mounts.has_key(mountPoint):
            self.mounts[mountPoint].append(fs)
        else:
            self.mounts[mountPoint]=[fs]
            self._mountpoints.append(mountPoint)
            self._sortMountPoints()

    def find_mount(self, path, strict=0):
        found=None
        # because of dynamic mounting, these need to be re-sorted
        # at find_mount invocation time, which is too bad
        self._sortMountPoints()
        # these are kept sorted longest first
        for p in self._mountpoints:
            ps=str(p)
            if path.startswith(ps):
                found=p
                break
        if not found:
            raise VFSException, "no mount point found for path %s" % path
        
        # for each fs mounted at that point, try to locate the file; if
        # an exception occurs, try the next, and so on.
        translatedPath=pathjoin('/', path[len(ps):])
        statinfo=None
        fs=None
        for tmp in self.mounts[found]:
            try:
                statinfo=tmp.vstat(translatedPath)
                fs=tmp
                break
            except:
                continue
        # file not found; fs and statinfo should both be None
        if None==statinfo and strict:
            raise FileNotFoundException, path
        else:
            return found, fs, translatedPath, statinfo
    
    def vstat(self, path):
        found, fs, translated, stat=self.find_mount(path, 1)
        return stat

    def listdir(self, dir):
        if not dir.endswith('/'):
            dir='%s/' % dir
        found, fs, translated, stat=self.find_mount(dir, 1)
        listing=fs.listdir(translated)
        mounts=map(lambda x, y=dir: x[len(y):],
                   containedPaths(map(str, self._mountpoints),
                                  dir))

        def cleanpath(path):
            path=frontslashRE.sub('', path)
            path=endslashRE.sub('', path)
            return path
        listing.extend(map(cleanpath, mounts))
        listing.sort()
        return listing

    def isdir(self, path):
        found, fs, translated, stat=self.find_mount(path, 1)
        return fs.isdir(translated)

    def isfile(self, path):
        found, fs, translated, stat=self.find_mount(path, 1)
        return fs.isfile(translated)        

    def remove(self, path):
        found, fs, translated, stat=self.find_mount(path, 1)
        fs.remove(translated)

    def open(self, path, mode='r'):
        """
        returns a file object.  
        """
        found, fs, translated, stat=self.find_mount(path, 0)
        # file was found
        if stat!=None and fs !=None:
            return fs.open(translated, mode)
        # file was not found
        if mode=='r':
            # file should have existed, raise
            raise FileNotFoundException, path
        # append or write mode; find a suitable fs
        for tmp in self.mounts[found]:
            try:
                return tmp.open(path, mode)
            except:
                continue
        raise NotWriteableException, "cannot open file: %s with mode: %s" % (path, mode)


__all__=['VST_SIZE',
         'VST_MTIME',
         'VST_ATIME',
         'VST_CTIME',
         'VFSRegistry',
         'FS',
         'LocalFS',
         'MultiFS',
         'VFSException',
         'FileNotFoundException',
         'NotWriteableException']
