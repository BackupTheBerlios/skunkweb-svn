

from bisect import insort_right
from threading import RLock
import fnmatch
import os
import re
from skunk.util.decorators import with_lock

# private helper function for decorator
def _getlock(self, *args, **kwargs):
    return self._lock
 
class ScopeManager(object):
    """
    The ScopeManager object manages configuration that changes
    depending on a context dictionary.
    
    The effective value of the configuration depends on:
    
    * the default configuration dictionary
    * scope matchers, which cause configuration to vary according
      to the environment
    * the context, which you pass to the getConfig() function.
    
    To get the current configuration values, call getConfig(context).

    """

    def __init__(self):
        self._lock=RLock()
        self.defaults={}
        self.matchers=[]

    def mergeDefaults(self, **kw):
        """ sets default values for the defaults."""
        for k in kw:
            self.defaults.setdefault(k, kw[k])

    @with_lock(_getlock)
    def getConfig(self, context):
        """ returns a dictionary with the current configuration. """
        config=self.defaults.copy()
        for m in self.matchers:
            self._processMatcher(m, context, config)
        return config

    def _processMatcher(self, matcher, context, overlay):
        if (context.has_key(matcher.param) 
            and matcher.match(context)
            and matcher.overlay):
            overlay.update(matcher.overlay)
        for kid in matcher.children:
            self._processMatcher(kid, context, overlay)

    def load(filename):
        """loads configuration from a file."""
        filename=os.path.abspath(filename)
        co=compile(s, filename, 'exec')
        exec codeObj in {}, self.defaults

    def scope(self, *matchers):
        """adds scope matchers"""
        self.matchers.extend(matchers)

class ScopeMatcher(object):
    """
    A ScopeMatcher object can be added to a ScopeManager through its
    scope() method.
    """
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

    def addChildren(self, *kids):
        """
        adds ScopeMatcher(s) to the list of children,
        keeping it sorted.
        """
        for k in kids:
            insort_right(self._children, k)

    def __cmp__(self, other):
        if isinstance(other, ScopeMatcher):
            return cmp((self.param, self.matchObj),
                       (other.param, other.matchObj))
        else:
            # who cares
            return cmp(str(self), str(other))

class CondMatcher(ScopeMatcher):
    """A matcher is which the match object is a callable that
    takes one argument and returns a boolean indicating whether the
    value matches."""
    def _match(self, other):
        return self.matchObj(other)

class InMatcher(ScopeMatcher):
    """A matcher in which the match object is a list, set, iterator or
    other other object that implements the __contains__ protocol, and
    the match succeeds if the matched value is in the container."""
    
    def _match(self, other):
        return other in self.matchObj

class StrictMatcher(ScopeMatcher):
    """A matcher in which the matched value must equal matchObj for
    there to be a match."""

    def _match(self, other):
        return self.matchObj==other

class SimpleStringMatcher(ScopeMatcher):
    """A matcher in which there is a match if the matched value
    startswith the match object."""
    
    def _match(self, other):
        return isinstance(other, basestring)\
               and other.startswith(self.matchObj)

class GlobMatcher(ScopeMatcher):
    """A matcher in which there is a match if the matched value
    matches a glob passed as the match object.
    """
    def _match(self, other):
        return isinstance(other, basestring)\
               and fnmatch.fnmatchcase(other, self.matchObj)

class RegexMatcher(ScopeMatcher):
    """A matcher in which matchObj is compiled into a regular expression
    and the match succeeds if the regex matches the matched value."""

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

        
    
__all__=['ScopeManager',
         'ScopeMatcher',
         'CondMatcher',
         'InMatcher',
         'StrictMatcher',
         'SimpleStringMatcher',
         'GlobMatcher',
         'RegexMatcher']
