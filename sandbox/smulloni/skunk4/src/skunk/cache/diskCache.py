import os
from os.path import (normpath,
                     expanduser,
                     abspath,
                     exists,
                     join as pathjoin,
                     dirname,
                     isdir,
                     walk as pathwalk)
from shutil import rmtree
import time
import cPickle
import errno
import tempfile

from skunk.cache.base import Cache
from skunk.cache.log import debug

class DiskCache(Cache):
    def __init__(self, path):
        p=abspath(expanduser(path))
        if not exists(p):
            os.makedirs(p)
        else:
            if not isdir(p):
                raise ValueError, \
                      "not a directory: %s (%s)" % (path, p)
            if not os.access(p, os.R_OK | os.W_OK):
                raise ValueError, \
                      "improper permissions for path: %s (%s)" % (path, p)
        self.path=p

    def _path_for_name(self, canonicalName):
        b=canonicalName.split('.')
        return normpath('%s/%s' % (self.path,
                                   '/'.join(b)))

    def _path_for_name_and_key(self, canonicalName, cacheKey):
        b=canonicalName.split('.')
        l=min(len(cacheKey), 6)
        b.extend([cacheKey[x:x+2] for x in range(0, l, 2)])
        b.append(cacheKey)
        return normpath('%s/%s' % (self.path,
                                   '%s.cache' % '/'.join(b)))

    def _retrieve(self, canonicalName, cacheKey):
        p=self._path_for_name_and_key(canonicalName, cacheKey)
        try:
            f=file(p)
        except IOError, e:
            if e.errno==errno.ENOENT:
                # not in cache
                return None
            else:
                # some other problem
                raise
        else:
            return cPickle.load(f)

    def _store(self, entry, canonicalName, cacheKey):
        entry.stored=time.time()
        p=self._path_for_name_and_key(canonicalName, cacheKey)
        debug("cache path is %r", p)
        dname=dirname(p)
        try:
            os.makedirs(dname)
        except OSError, e:
            if e.errno!=errno.EEXIST:
                raise
        fd, tempname=tempfile.mkstemp(suffix=".tmp",
                                      dir=dname)
        tempf=os.fdopen(fd, 'w')
        cPickle.dump(entry, tempf)
        tempf.close()
        os.rename(tempname, p)
        
    def invalidate(self, canonicalName):
        """
        removes cache entries for the canonicalName.
        This does not actually delete the cache entries, but
        renames them. 
        """
        p=self._path_for_name(canonicalName)
        dname=dirname(p)
        # we need a name that isn't in use;
        # the same canonicalName may be invalidated
        # multiple times between cache clears.
        tempname=tempfile.mkdtemp(suffix=".del",
                                  dir=dname)
        os.rename(p, tempname)

    def pack(self):
        """
        deletes all invalidated entries
        """

        def walker(arg, dname, fnames):
            if dname.endswith('.del'):
                rmtree(dname)
        pathwalk(self.path, walker, None)
            


__all__=['DiskCache']
