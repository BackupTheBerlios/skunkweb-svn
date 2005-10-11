from os.path import splitext, dirname, join as pathjoin

from skunk.components.component import *

class ComponentHandler(object):
    """
    abstract base class for component handlers
    """
    protocols=[]

    def getComponentClass(self,
                          protocol,
                          componentHandle,
                          componentType):
        """
        returns the appropriate component class for the
        createComponent call
        """
        raise NotImplemented

    def inferComponentType(self, componentHandle):
        """
        if possible, infer the component type from the handle,
        or raise ValueError.
        """
        raise ValueError, "cannot infer component type"

    def instantiateComponent(self,
                             factory,
                             kls,
                             componentHandle,
                             namespace,
                             componentCache,
                             compileCache,
                             extra_globals,
                             **extra):
        return kls(componentHandle,
                   factory=factory,
                   namespace=namespace,
                   componentCache=componentCache,
                   compileCache=compileCache,
                   extra_globals=extra_globals,
                   **extra)

    
    def createComponent(self,
                        factory,
                        protocol,
                        componentHandle,
                        componentType,
                        namespace=None,
                        componentCache=None,
                        compileCache=None,
                        extra_globals=None,
                        **extra):
        if protocol not in self.protocols:
            raise ValueError, "unsupported protocol: %s" % protocol
        if componentType is None:
            # this should raise a ValueError if the type cannot
            # inferred; it shouldn't return None
            componentType=self.inferComponentType(componentHandle)
            assert componentType
        kls=self.getComponentClass(protocol,
                                   componentHandle,
                                   componentType)
        stack=factory.componentStack
        if (not namespace) and componentType=='include':
            if not stack:
                raise ComponentHandlingException,\
                      "include not possible without something on component stack!"
            namespace=stack[-1].namespace

        if extra_globals is None:
            extra_globals=factory.extra_globals

        return self.instantiateComponent(factory,
                                         kls,
                                         componentHandle,
                                         namespace,
                                         componentCache,
                                         compileCache,
                                         extra_globals,
                                         **extra)


class CallableComponentHandler(ComponentHandler):
    """
    A component handler for generic callables.
    """
    protocols=['callable']

    def getComponentClass(self,
                          protocol,
                          componentHandle,
                          componentType):
        """
        returns the appropriate component class for the
        createComponent call
        """
        if componentType in ('string', 'include'):
            return StringOutputComponent
        elif componentType=='data':
            return Component
        raise ValueError, "unknown component type: %s" % componentType

    def instantiateComponent(self,
                             factory,
                             kls,
                             componentHandle,
                             namespace,
                             componentCache,
                             compileCache,
                             extra_globals,
                             **extra):
        if isinstance(componentHandle, tuple):
            name=componentHandle[0]
            code=componentHandle[1]
        else:
            name=getattr(componentHandle,
                         '__name__',
                         repr(componentHandle))
            code=componentHandle
        return kls(code=componentHandle,
                   name=name,
                   namespace=namespace,
                   componentCache=componentCache,
                   compileCache=compileCache,
                   factory=factory,
                   extra_globals=extra_globals
                   **extra)


DEFAULT_FILE_COMPONENT_SUFFIX_MAP={'.pycomp' : ('string',StringOutputFileComponent),
                                   '.pydcmp' : ('data', FileComponent),
                                   '.pyinc' : ('include', StringOutputFileComponent)}

class LocalFileComponentHandler(ComponentHandler):
    """
    a component handler for file components.
    """
    protocols=['file']
    
    def __init__(self, suffixMap=None):
        if suffixMap is None:
            suffixMap=DEFAULT_FILE_COMPONENT_SUFFIX_MAP
        self.suffixMap=suffixMap

    def getComponentClass(self,
                          protocol,
                          componentHandle,
                          componentType):
        compClass=self._lookup_suffix(componentHandle)[1]
        if compClass:
            return compClass
        else:
            raise ValueError, "no handler for handle: %r" % componentHandle
            

    def _lookup_suffix(self, handle):
        return self.suffixMap.get(splitext(handle)[1], (None, None))
    
    def inferComponentType(self, componentHandle):
        compType=self._lookup_suffix(componentHandle)[0]
        if compType:
            return compType
        else:
            raise ValueError, \
                  "cannot infer component type from file name %r" % componentHandle

    def instantiateComponent(self,
                             factory,
                             kls,
                             componentHandle,
                             namespace,
                             componentCache,
                             compileCache,
                             extra_globals,
                             **extra):
        componentHandle=self.rectifyRelativePath(componentHandle, factory)
        return kls(componentHandle,
                   namespace=namespace,
                   componentCache=componentCache,
                   compileCache=compileCache,
                   factory=factory,
                   extra_globals=extra_globals,
                   **extra)

    def rectifyRelativePath(self, path, factory):
        if path.startswith('/'):
            return path
        cwd=factory.getCurrentDirectory()
        if not cwd:
            raise ComponentHandlingException, \
                  ("cannot invoke a component with a relative path without a "
                   "prior file context")
        return pathjoin(cwd, path)


__all__=['ComponentHandler',
         'LocalFileComponentHandler',
         'CallableComponentHandler',
         'DEFAULT_FILE_COMPONENT_SUFFIX_MAP']
