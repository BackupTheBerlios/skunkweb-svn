from bisect import insort_right
from threading import Lock
import fnmatch
import os
import re

from skunk.util.decorators import with_lock

# helper function for decorator
def _getlock(self, *args, **kwargs):
    return self._lock

class ScopedConfig(object):
    """


    """

    def __init__(self):
        self.defaults={}
        self._scopes={}
        self._stack=[]
        self.matchers=[]
        self._lock=Lock()

    @with_lock(_getlock)
    def mergeDefaults(self, **kw):
        """ """
        for k in kw:
            self.defaults.setdefault(k, kw[k])

    @with_lock(_getlock)
    def mash(self):
        """ """
        masher=self.defaults.copy()
        for d in self._stack:
            masher.update(d)
        return masher

    @with_lock(_getlock)
    def scope(self, d):
        """ TBD """
        current=self._scopes
        current.update(d)
        scopedict={}
        for m in self.matchers:
            self._processMatcher(m, scopedict, d)
            if scopedict:
                self.push(scopedict)

    def _processMatcher(self, matcher, scopedict, valdict):
        if (valdict.has_key(matcher.param) 
            and matcher.match(valdict)
            and matcher.overlay):
            scopedict.update(matcher.overlay)
        for kid in matcher.children:
            self._processMatcher(kid, scopedict, valdict)
            
    def push(self, d):
        """ """
        self._stack.append(d)

    def pop(self):
        """ """
        return self._stack.pop()

    def trim(self):
        """ """
        del self._stack[:]

    @with_lock(_getlock)
    def load_from_file(filename):
        filename=os.path.abspath(filename)
        co=compile(s, filename, 'exec')
        exec codeObj in {}, self.defaults

                

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


# TODO:
#   docstrings,
#   cleanup.
#   Other matchers.
#   reading from config file (ConfigLoader functionality)
#   dumping a mash into a thread local.
#
# then, server integration.
        
