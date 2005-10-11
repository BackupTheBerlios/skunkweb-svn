from os.path import normpath, join as pathjoin
import re

_adjust_pattern=re.compile('//*$')
_double_slash_pattern=re.compile('//*')
_slash_pattern=re.compile('^/')
_final_slash_pattern=re.compile('/*$')

def adjust_user_path(path, prefix='/'):
    "removes slashes at end of path and roots it under prefix"
    s=pathjoin(prefix, _adjust_pattern.sub('', path))
    return _double_slash_pattern.sub('/', s)

def deslash_path(path):
    "removes slash at beginning"
    return _slash_pattern.sub('', path)

def impliedPaths(paths):
    """
    given a list of paths, returns a list of all implied paths in a unix-style
    filesystem.  Hence, given ["/foo/bar/goo", "/loo/moo/shoe"], returns
    ['/', '/foo', '/foo/bar', '/loo', '/loo/moo']
    """
    implied=[]
    deslashedPaths=map(lambda x: x.endswith('/') and x[:-1] or x, paths)
    for p in deslashedPaths:
        elems=p.split('/')
        for i in range(len(elems)):
            dir=pathjoin('/', '/'.join(elems[:i]))
            if dir not in deslashedPaths and dir not in implied:
                implied.append(dir)
    return implied


def containedPaths(names, dir):
    dir=_final_slash_pattern.sub('/', dir)
    return filter(lambda x, y=dir: x.startswith(y) \
                  and y!=x \
                  and '/' not in x[len(y):-1],
                  names)

def listdir(path, archive_listing):
    adjusted=adjust_user_path(path)
    return map(lambda x, y=adjusted, r=_slash_pattern: r.sub('', x[len(y):]),
               containedPaths(archive_listing, adjusted))


class Archive(object):
    """
    does some of the non-archive-format related dirty work
    in managing an archive file
    """

    def __init__(self, root='/', prefix='/'):
        self.root=root
        self.prefix=prefix

    def _resolvepath(self, path):
        return normpath('%s/%s' % (self.root, path))
        
    def savePaths(self, namelist):
        self.paths={}
        rootlen=len(self.root)
        nl=[(x[rootlen:], x) for x in namelist if x.startswith(self.root)]
        for name, realname in nl:
            adjusted=adjust_user_path(pathjoin(self.prefix, name))
            self.paths[adjusted]=realname
        implied=impliedPaths(self.paths.keys())
        for name in implied:
            self.paths[name]=None

    def exists(self, path):
        return self.paths.has_key(adjust_user_path(path))

    def listdir(self, path):
        return listdir(path, self.paths.keys())

__all__=[]
