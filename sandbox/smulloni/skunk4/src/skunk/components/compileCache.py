"""

This contains a Cache implementation for storing the
compiled code of components.  It is used internally
in the Component class, and an instance can be
passed to a Component constructor.

  >>> c=CompileCache('/path/to/cacheroot', useMemory=True)
  >>> component=FileComponent(mypath, compileCache=c)

The cache can store compiled code on disk, in memory, or both.

"""

import os
import errno
import stat
import time
import marshal
normpath=os.path.normpath

def _mtime(path):
    try:
        s=os.stat(path)
    except OSError, e:
        if e.errno!=errno.ENOENT: 
           raise
        return None 
    else:
        return max(s[stat.ST_CTIME],
                   s[stat.ST_MTIME])

class CompileCache(object):
    def __init__(self,
                 cacheroot,
                 useMemory=True):
        if (not cacheroot) and not useMemory:
            raise ValueError, "must use either disk or memory caching, or both"
        self.cacheroot=cacheroot
        self.useMemory=useMemory
        if useMemory:
            self._mem={}

    def getCompiledCode(self, component):
        # is the component file-based?
        try:
            lastmod=component.__lastmodified__
        except AttributeError:
            lastmod=None

        entry=self._retrieve(component.name)
        if entry:
            cachemod, code=entry
            if lastmod is None or lastmod<=cachemod:
                return code

        code=component.compile(component.getCode())
        self._store(component.name, code)
        return code

    def _retrieve(self, name):
        if self.useMemory:
            try:
                return self._mem[name]
            except KeyError:
                pass
        if self.cacheroot:
            f=normpath('%s/%sc' % (self.cacheroot, name))
            cachemod=_mtime(f)
            if cachemod:
                stuff=file(f).read()
                code=marshal.loads(stuff)
                if self.useMemory:
                    self._mem[name]=cachemod, code
                return cachemod, code

    def _store(self, name, code):
        if self.useMemory:
            self._mem[name]=(time.time(), code)
        if self.cacheroot:
            f=normpath('%s/%sc' % (self.cacheroot, name))
            d=os.path.dirname(f)
            if not os.path.exists(d):
                os.makedirs(os.path.dirname(f))
            fp=file(f, 'wb')
            fp.write(marshal.dumps(code))
            fp.close()


__all__=['CompileCache']
