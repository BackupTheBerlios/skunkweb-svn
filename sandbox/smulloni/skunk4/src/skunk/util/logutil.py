import logging
import sys

def loginit(name=None, offset=1, strip_package=True, make_all=True):
    """method for generating a module with log methods using the logger
    for a particular package or module."""
    if name is None:
        name=__name__
    if strip_package and '.' in name:
        name=name[:name.rfind('.')]
    g=sys._getframe(offset).f_locals
    l=logging.getLogger(name)
    all=('critical',
         'debug',
         'error',
         'exception',
         'info',
         'log',
         'warn')
    g['logger']=l
    for x in all:
        g[x]=getattr(l,x)
    if make_all:
        g['__all__']=all + ('logger',)
    
