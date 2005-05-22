import os
from os.path import normpath
import time
import cPickle
import errno
import tempfile

from skunk.cache.base import Cache
from skunk.cache.log import debug

class DiskCache(Cache):
    def __init__(self, cachePath):
        if not os.path.isdir(cachePath):
            raise ValueError, "not a directory: %s" % cachePath
        if not os.access(cachePath, os.R_OK | os.W_OK):
            raise ValueError, "improper permissions for path: %s" % cachePath
        self.cachePath=cachePath

    def _path_for_name(self, canonicalName):
        b=canonicalName.split('.')
        return normpath('%s/%s' % (self.cachePath,
                                   '/'.join(b)))

    def _path_for_name_and_key(self, canonicalName, cacheKey):
        b=canonicalName.split('.')
        l=min(len(cacheKey), 6)
        b.extend([cacheKey[x:x+2] for x in range(0, l, 2)])
        b.append(cacheKey)
        return normpath('%s/%s' % (self.cachePath,
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
        dirname=os.path.dirname(p)
        try:
            os.makedirs(dirname)
        except OSError, e:
            if e.errno!=errno.EEXIST:
                raise
        fd, tempname=tempfile.mkstemp(suffix=".tmp",
                                      dir=dirname)
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
        dirname=os.path.dirname(p)
        # we need a name that isn't in use;
        # the same canonicalName may be invalidated
        # multiple times between cache clears.
        tempname=tempfile.mkdtemp(suffix=".del",
                                  dir=dirname)
        os.rename(p, tempname)


__all__=['DiskCache']
