"""
The ScopedConfig object manages configuration that changes depending on a context dictionary.

The effective value of the configuration depends on:

  * the default configuration dictionary
  * scope matchers, which cause configuration to vary according to the environment
  * the context dictionary

To get the current configuration values, call mash(), which returns a dictionary.

TODO:

   simplify this drastically.  The only state the object should store
   is the matchers (the configuration). Don't store the context in the
   object at all; it is just a dictionary.  Don't store the overlay
   either; mash() will pass in (or have passed in into it) a
   container.  "mash" is also a dumb name since there isn't anything
   to mash, anymore.

   I'm checking this in just so I don't lose it; the next version will
   be quite different.

"""


from bisect import insort_right
from threading import Lock
import fnmatch
import os
import re

from skunk.util.decorators import with_lock, _share_metadata, call_super

# private helper function for decorator
def _getlock(self, *args, **kwargs):
    return self._lock

def adjustconfig(fn):
    """a decorator to enforce that mutation operations on data
    structures are followed by appropriate adjustments to the config
    object that owns them"""
    def wrapper(self, *args, **kwargs):
        ret=fn(self, *args, **kwargs)
        self._config._adjust()
        return ret
    _share_metadata(fn, wrapper)
    return wrapper

class _contextdict(dict):
    def __new__(cls, config):
        return dict.__new__(cls)
    
    def __init__(self, config):
        self._config=config
        self._lock=config._lock

    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def __setitem__(self, item, value):
        pass

    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def __delitem__(self, item):
        pass

    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def clear(self):
        pass
        

    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def update(self, d):
        pass

    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def setdefault(self, key, failobj=None):
        pass

    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def pop(self, key, *args):
        pass

    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def popitem(self):
        pass


class _matcherlist(list):
    def __new__(cls, config):
        return list.__new__(cls)

    def __init__(self, config):
        super(_matcherlist, self).__init__()
        self._config=config
        self._lock=config._lock

    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def __setitem__(self, i, item):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def __delitem__(self, i):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def __setslice__(self, i, j, other):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def __delslice__(self, i, j):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def append(self, item):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def insert(self, i, item):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def pop(self, i=-1):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def remove(self, item):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def reverse(self):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def sort(self, *args, **kwds):
        ""
    @with_lock(_getlock)
    @adjustconfig
    @call_super
    def extend(self, other):
        ""

    def __imul__(self, n):
        raise NotImplementedError

    def __mul__(self, n):
        raise NotImplementedError
    
    def __iadd__(self, n):
        self.append(n)

    def __radd__(self, other):
        raise NotImplementedError
    
class ScopedConfig(object):
    """


    """

    def __init__(self):
        self._lock=Lock()
        self.defaults={}
        self.context=_contextdict(self)
        self.matchers=_matcherlist(self)

        self._overlay={}

    @with_lock(_getlock)
    def mergeDefaults(self, **kw):
        """ """
        for k in kw:
            self.defaults.setdefault(k, kw[k])

    @with_lock(_getlock)
    def mash(self):
        """ returns a dictionary with the current configuration. """
        mashed=self.defaults.copy()
        mashed.update(self._overlay)
        return mashed


    def _adjust(self):
        """ private function called by other functions that
        change the context. Those functions should be synchronized;
        this is not."""
        self._overlay.clear()
        for m in self.matchers:
            self._processMatcher(m)

    def _processMatcher(self, matcher):
        valdict=self.context
        scopedict=self._overlay
        if (valdict.has_key(matcher.param) 
            and matcher.match(valdict)
            and matcher.overlay):
            scopedict.update(matcher.overlay)
        for kid in matcher.children:
            self._processMatcher(kid)

    def trim(self):
        """remove all scopes"""
        self.context.clear()

    @with_lock(_getlock)
    def Include(filename):
        """loads configuration from a file."""
        filename=os.path.abspath(filename)
        co=compile(s, filename, 'exec')
        exec codeObj in {}, self.defaults

    def Scope(self, *matchers):
        """adds scope matchers"""
        self.matchers.extend(matchers)

class ScopeMatcher(object):
    def __init__(self, param, matchObj, overlay, children=None):
        self.param=param
        self.matchObj=matchObj
        self.overlay=overlay
        if children:
            self._children=children[:]
            self._children.sort()
        else:
            self._children=[]


    def _match(self, other):
        """
        subclasses should implement this.
        """
        raise NotImplementedError

    def match(self, paramdict):
        return self._match(paramdict.get(self.param, None))

    def children(self):
        """
        this gives you a COPY of the matcher's list of children.
        You don't get the original, because it needs to be kept
        sorted, and I don't want to have to perform the sort
        redundantly, for safety, every time a match is performed.
        Use addChildren to add matchers to the list and the sort will
        be performed then, automagical-like.
        """
        return self._children[:]
    children=property(children)

    def addChildren(self, *kids):
        """
        adds ScopeMatcher(s) to the list of children,
        keeping it sorted.
        """
        for k in kids:
            insort_right(self._children, k)


    def __str__(self):
        return "%s : %s (%s %s)" % (self.param,
                                   self.matchObj,
                                   self.overlay,
                                   self.children)

    def __repr__(self):
        return "<%s.%s instance: %s>" % (self.__class__.__module__,
                                         self.__class__.__name__,
                                         self)

    def __hash__(self):
        return hash((self.param, self.matchObj))

    def __cmp__(self, other):
        if isinstance(other, ScopeMatcher):
            # I don't want two different matchers whose top level is
            # identical to exist in the same dictionary, regardless of
            # their match type.
            return cmp((self.param, self.matchObj),
                       (other.param, other.matchObj))
        else:
            # who cares
            return cmp(str(self), str(other))

class CondMatcher(ScopeMatcher):

    def _match(self, other):
        return self.matchObj(other)

class InMatcher(ScopeMatcher):

    def _match(self, other):
        return other in self.matchObj

class StrictMatcher(ScopeMatcher):

    def _match(self, other):
        return self.matchObj==other

class SimpleStringMatcher(ScopeMatcher):
    
    def _match(self, other):
        return isinstance(other, basestring)\
               and other.startswith(self.matchObj)

class GlobMatcher(ScopeMatcher):
    
    def _match(self, other):
        return isinstance(other, basestring)\
               and fnmatch.fnmatchcase(other, self.matchObj)

class RegexMatcher(ScopeMatcher):

    def __init__(self, matchObj, overlay, children=[]):
        ScopeMatcher.__init__(self, matchObj, overlay, children)
        self._compiledRegex=re.compile(self.matchObj)

    def _match(self, other):
        return isinstance(other, basestring)\
               and self._compiledRegex.match(other)


def _createMatcher(matcherClass, paramName, paramVal, kids, kw):
    m=matcherClass(paramName, paramVal, kw)
    if kids:
        m.addChildren(*kids)
    return m

        
    


# TODO:
#   docstrings,
#   cleanup.
#   Other matchers.
#   reading from config file (ConfigLoader functionality)
#   dumping a mash into a thread local.
#
# then, server integration.
        
