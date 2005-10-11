import cStringIO
import re
from types import CodeType

from skunk.cache.policy import NO
from skunk.vfs import LocalFS

class ComponentHandlingException(Exception):
    pass

class ComponentArgumentError(ValueError):
    pass

class ReturnValue(Exception):
    """
    An exception class for sending return values out of data components.
    """
    def value(self):
        if self.args:
            return self.args[0]
    value=property(value, None, None, None)


class Component(object):
    """
    A Component is a callable wrapper around a code object which
    manages the namespace in which the callable is executed.
    Additionally, facilities are provided for the memoization of the
    return values of Components (using the skunk.cache package) and
    the caching of compiled component code (using the
    skunk.components.compileCache module).

    The namespace of a Component instance may be changed by calling
    the component.  Individual Component instances should not be
    used concurrently.  For these reasons, instances are intended
    to be created, used once, and then thrown away in normal use.

    Normally, you don't create a Component directly, but create
    instances by calling the createComponent() method of a
    ComponentFactory.
    """
    def __init__(self,
                 code,
                 name=None,
                 namespace=None,
                 componentCache=None,
                 compileCache=None,
                 factory=None,
                 extra_globals=None):
        if name is None:
            try:
                name=code.__name__
            except AttributeError:
                name="?"
        self.__cachename__=self.name=name
        self._code=code
        if namespace is None:
            self.namespace={}
        else:
            self.namespace=namespace

        if compileCache is None:
            if factory:
                compileCache=factory.compileCache
        self.compileCache=compileCache
        if componentCache is None:
            if factory:
                componentCache=factory.componentCache
        self.componentCache=componentCache
        self.factory=factory
        if factory:
            self.componentStack=factory.componentStack
        else:
            self.componentStack=[]
        self.extra_globals=extra_globals or {}

        # private
        self._nocache=False
        self._current_args=None

    def check_args(self, args, kwargs):
        """
        checks whether the component arguments correspond to an
        expected signature.  Required arguments are stated as string
        values in the tuple-or-list "args", which may also include one
        spillover variable, which should start with two asterisks.
        Optional arguments should be put in the dictionary "kwargs",
        with the default values as keys.  The component namespace will
        be updated with the default values of any arguments that have
        not been passed, and with the spillover variable (without the
        two asterisks), if it exists, added to the namespace
        associated with a dictionary of any spillover arguments.  If a
        required argument is not provided, a ComponentArgumentError
        will be raised; if a duplicate argument name occurs in the
        signature specification, or more than one spillover argument,
        a ValueError will be raised.
        """
        compargs=self._current_args
        spillover=None
        required=[]
        for a in args:
            if a in required or a==spillover:
                raise ValueError, "duplicate argument: %s" % a
            if a.startswith('**'):
                if spillover:
                    raise ValueError, "only one spillover argument allowed: %s" % a
                spillover=a[2:]
                if spillover in required:
                    raise ValueError, "duplicate argument: %s" % a
            else:
                required.append(a)
        for k, v in kwargs.items():
            if k in required or k == spillover:
                raise ValueError, "duplicate argument: %s" % k
        spilldict={}
        for n in compargs:
            if n in required:
                required.remove(n)
            elif n in kwargs:
                del kwargs[n]
            elif spillover:
                spilldict[n]=compargs[n]
            else:
                raise ComponentArgumentError, "unexpected argument: %s" % n
        if required:
            if len(required)==1:
                msg="expected argument not passed: %s" % required[0]
            else:
                msg="expected arguments not passed: %s" % ", ".join(required)
            raise ComponentArgumentError, msg
        if kwargs:
            self.namespace.update(kwargs)
        if spillover:
            self.namespace[spillover]=spilldict
        
    def callComponent(self,
                      componentHandle,
                      compArgs=None,
                      cachePolicy=NO,
                      expiration=None,
                      componentType=None,
                      namespace=None,
                      componentCache=None):
        """
        convenience method for calling a component
        from within this one.
        """
        if not self.factory:
            raise ComponentHandlingException, \
                  "cannot call nested component without component factory"
        comp=self.factory.createComponent(componentHandle,
                                          componentType,
                                          namespace,
                                          componentCache)
        if expiration is None:
            expiration=self.factory.defaultExpiration
        return comp(compArgs, cachePolicy, expiration)
                      
    def callStringComponent(self,
                            componentHandle,
                            compArgs=None,
                            cachePolicy=NO,
                            expiration=None,
                            namespace=None,
                            componentCache=None):
        """
        convenience method for calling a string component
        from within this one 
        """
        return self.callComponent(componentHandle,
                                  compArgs,
                                  cachePolicy,
                                  expiration,
                                  'string',
                                  namespace,
                                  componentCache)

    def callDataComponent(self,
                          componentHandle,
                          compArgs=None,
                          cachePolicy=NO,
                          expiration=None,
                          namespace=None,
                          componentCache=None):
        """
        convenience method for calling a data component
        from within this one 
        """        
        return self.callComponent(componentHandle,
                                  compArgs,
                                  cachePolicy,
                                  expiration,
                                  'data',
                                  namespace,
                                  componentCache)

    def callIncludeComponent(self, componentHandle):
        """
        convenience method for calling an include component
        from within this one 
        """        
        return self.callComponent(componentHandle, componentType='include')


    def getCode(self):
        """
        returns the code object the component wraps.
        """
        return self._code

    def _get_code_raw(self):
        return self._code

    def getCompiledCode(self):
        """
        returns the compiled form of the code object the component
        wraps, accessing it from a compile cache if the component is
        using one.
        """
        code=self.getCode()
        if isinstance(code, CodeType):
            return code
        cache=self.compileCache
        if cache:
            return cache.getCompiledCode(self)
        else:
            return self.compile(code)

    def compile(self, codeObj):
        """
        compiles the component's code; called by subclasses.
        """
        return compile(codeObj, self.name, 'exec')

    def _precall(self, namespace):
        """
        a hook for subclass to munge the namespace before the real
        call of the component code; returns the munged namespace
        """
        return namespace

    def _postcall(self, value, namespace):
        """
        any introspection you want to perform in the class about the
        result of calling can be done here, as well as arbitrary
        munging
        """
        return value

    def __call__(self,
                 compArgs=None,
                 cachePolicy=NO,
                 expiration=None):
        cache=self.componentCache
        if self._nocache or cachePolicy==NO or not cache:
            return self._real_call(compArgs)
        else:
            self._nocache=True
            try:
                return cache.call(self,
                                  {'compArgs' : compArgs},
                                  cachePolicy,
                                  expiration).value
            finally:
                self._nocache=False

    def _real_call(self, compArgs=None):
        code=self.getCompiledCode()
        ns=self.namespace
        stack=self.componentStack
        
        self._current_args=compArgs or {}
        if compArgs:
            # add component arguments to namespace
            ns.update(compArgs)
        # add self to component stack
        stack.append(self)
        
        # add self to namespace as COMPONENT, saving the previous
        # value, if any.  Most of the time (almost always except with
        # includes) ns will be an empty dict, so I check with has_key
        # rather than catching KeyError (which is faster when that is
        # the expectation).
        if ns.has_key('COMPONENT'):
            oldcomp=(ns['COMPONENT'],)
        else:
            oldcomp=None
        ns['COMPONENT']=self
        ns.setdefault('ReturnValue', ReturnValue)
        # any special values you want to add to components in this stack
        ns.update(self.extra_globals)
        # sub-class specific component namespace munging
        ns=self._precall(ns)
        val=None        
        try:
            exec code in ns
        except ReturnValue, rv:
            val=rv.value

        # if the component code blows up, we leave the component stack
        # with all the affected components on it, so as to be able to
        # get a full traceback; otherwise, we pop components off
        # the stack when we are done. 
        stack.pop()
        
        # restore the previous component to the namespace, for the
        # sake of includes
        if oldcomp:
            ns['COMPONENT']=oldcomp[0]
        else:
            del ns['COMPONENT']
        
        return self._postcall(val, ns)

    def expiration(self):
        exp=self.namespace.get('__expiration')
        if (exp is None) and self.factory:
              exp=self.factory.defaultExpiration
        return exp
    
    expiration=property(expiration,
                        None,
                        None,
                        "the timestamp when the component output should expire in a cache")
    

isValidIdentifierPat=re.compile("^[a-zA-Z][a-zA-Z1-9_]*$")

class FileComponent(Component):
    """
    A component whose code is stored in a file.
    """
    def __init__(self,
                 filename,
                 namespace=None,
                 componentCache=None,
                 compileCache=None,
                 fs=None,
                 factory=None,
                 extra_globals=None):
        Component.__init__(self,
                           code=None,
                           name=filename,
                           namespace=namespace,
                           componentCache=componentCache,
                           compileCache=compileCache,
                           factory=factory,
                           extra_globals=extra_globals)
        self.__file__=self.filename=filename
        if fs is None:
            if factory:
                fs=factory.fs
            else:
                fs=LocalFS()
        self.fs=fs

    def __lastmodified__(self):
        return self.fs.getmtime(self.filename)
    __lastmodified__=property(__lastmodified__,
                              None,
                              None,
                              "last modification time of the underlying file")

    def getCode(self):
        if not self._code:
            self._code=self._get_code_raw()
        return self._code

    def _get_code_raw(self):
        return self.fs.open(self.__file__).read()
        
class StringOutputComponentMixin(object):
    """
    A mixin that implements the management of the output stream used
    by subclasses StringOutputComponent and StringOutputFileComponent.
    """
    def __init__(self, streamName):
        if not isValidIdentifierPat.match(streamName):
            raise ValueError, "not a valid identifier: %s" % streamName
        self._streamName=streamName
        
    def _precall(self, namespace):
        namespace[self._streamName]=cStringIO.StringIO()
        return namespace

    def _postcall(self, val, namespace):
        # anything returned by ReturnValue is ignored!
        out=namespace.get(self._streamName)
        if out:
            return out.getvalue()

class StringOutputComponent(StringOutputComponentMixin, Component):
    """
    A component that returns a string written to a stream in the
    component namespace called OUTPUT, which is managed by the
    component class.
    """
    def __init__(self,
                 code,
                 name=None,
                 namespace=None,
                 componentCache=None,
                 compileCache=None,
                 factory=None,
                 extra_globals=None,
                 streamName='OUTPUT'):
        StringOutputComponentMixin.__init__(self, streamName)
        Component.__init__(self,
                           code=code,
                           name=name,
                           namespace=namespace,
                           componentCache=componentCache,
                           compileCache=compileCache,
                           factory=factory,
                           extra_globals=extra_globals)


class StringOutputFileComponent(StringOutputComponentMixin, FileComponent):
    """
    A file component that returns a string written to a stream in the
    component namespace called OUTPUT, which is managed by the
    component class.
    """
    def __init__(self,
                 filename,
                 namespace=None,
                 componentCache=None,
                 compileCache=None,
                 fs=None,
                 factory=None,
                 extra_globals=None,
                 streamName="OUTPUT"):
        StringOutputComponentMixin.__init__(self, streamName)
        FileComponent.__init__(self,
                               filename=filename,
                               namespace=namespace,
                               componentCache=componentCache,
                               compileCache=compileCache,
                               fs=fs,
                               factory=factory,
                               extra_globals=extra_globals)
            
__all__=['ReturnValue',
         'ComponentHandlingException',
         'ComponentArgumentError',
         'Component',
         'FileComponent',
         'StringOutputComponent',
         'StringOutputFileComponent']
