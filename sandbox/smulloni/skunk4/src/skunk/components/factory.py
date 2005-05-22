from os.path import dirname

from skunk.components.component import ComponentHandlingException
from skunk.vfs import LocalFS

class ComponentFactory(object):
    def __init__(self,
                 componentHandlers,
                 compileCache=None,
                 componentCache=None,
                 componentStack=None,
                 fs=None,
                 extra_globals=None,
                 defaultExpiration=None):
        self.componentHandlers=componentHandlers
        self.compileCache=compileCache
        self.componentCache=componentCache
        if componentStack is None:
            componentStack=[]
        self.componentStack=componentStack
        if fs is None:
            fs=LocalFS()
        self.fs=fs
        if extra_globals is None:
            extra_globals={}
        self.extra_globals=extra_globals
        self.defaultExpiration=defaultExpiration

    def _parse_handle(self, handle):
        if isinstance(handle, basestring):
            try:
                protocol, handle=handle.split('://', 1)
            except ValueError:
                # fall back on file handler
                return 'file', handle
            else:
                return protocol, handle
        elif callable(handle):
            return 'callable', handle
        else:
            raise ComponentHandlingException, \
                  'no way to handle %r' % handle

    def getCurrentDirectory(self):
        s=self.componentStack
        i=len(s)-1
        while i >= 0:
            try:
                return dirname(s[i].filename)
            except AttributeError:
                i-=1
        
    def createComponent(self,
                        componentHandle,
                        componentType=None,
                        namespace=None,
                        componentCache=None,
                        compileCache=None,
                        extra_globals=None):
        """
        creates a component instance on the basis of the
        provided arguments and the factory's registered
        componentHandlers.
        """
        protocol, handle=self._parse_handle(componentHandle)
        handler=self.componentHandlers.get(protocol)
        if not handler:
            raise ComponentHandlingException, \
                  "no handler for protocol: %s" % protocol
        return handler.createComponent(factory=self,
                                       protocol=protocol,
                                       componentHandle=handle,
                                       componentType=componentType,
                                       namespace=namespace,
                                       componentCache=componentCache,
                                       compileCache=compileCache,
                                       extra_globals=extra_globals)

__all__=['ComponentFactory']
