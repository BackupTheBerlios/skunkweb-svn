from md5 import new as md5_new
from cPickle import PickleError, dumps as cPickle_dumps
import sys
from time import time
from skunk.cache.log import debug
from skunk.cache.exceptions import NotInCache, UnCacheable, BypassCache
from threading import RLock
import warnings

from skunk.util.timeconvert import convert as time_convert

_lookup_lock=RLock()
_callable_lookup={}

class Cache(object):
    """
    abstract base class for cache implementations.
    """

    @staticmethod
    def _unpack_callargs(callargs):
        if callargs in (None, [], (), {}):
            return (), {}
        elif isinstance(callargs, dict):
            return (), callargs
        elif isinstance(callargs, (list, tuple)):
            if not len(callargs)==2:
                raise ValueError, \
                      "list or tuple of callargs must be of length 2, instead got length %d" \
                      % len(callargs)
            args, kwargs=callargs
            if not isinstance(args, (list, tuple)):
                raise ValueError, "expected list or tuple for args, got %r" % type(args)
            if not isinstance(kwargs, dict):
                raise ValueError, "expected dict for kwargs, got %r" % type(kwargs)
            return args, kwargs
        else:
            raise ValueError, """\
            callargs must be either a dict of keyword arguments
            or a 2-tuple, (positional arguments (list or tuple),
            keyword arguments (dict))."""

    def call(self,
             callee,
             callargs,
             policy,
             expiration=None,
             ondefer=None):
        """
        invokes the callee with callargs through the cache, with the
        given cache policy.  This is the main user-space method.  It
        returns a CacheEntry instance.  The entry will only be
        guaranteed to have storage if policy.store is true.
        """
        # the canonical name and cache key are needed both for
        # retrieve and store; just get them once
        debug("policy is %r", policy)
        if expiration is not None:
            expiration=time_convert(expiration)

        args, kwargs=self._unpack_callargs(callargs)

        if policy.defer and ondefer is None:
            warnings.warn("cache policy DEFER in use without a deferral callback")
        
        if policy.retrieve or policy.store:
            cn=self.getCanonicalName(callee)
            ck=self.getCacheKey((args, kwargs), False)            
        
        if policy.retrieve:
            # has the callee changed since last checked?
            self.validateCallable(callee, cn)
            
            # get the cache entry if it exists
            entry=self._retrieve(cn, ck)
            if entry and policy.accept(entry):
                entry.retrieved=time()
                if policy.defer and ondefer:
                    return ondefer(entry, callee, callargs, expiration)
                return entry

        if policy.calculate or policy.defer:
            # the callee can bypass the cache by raising a BypassCache
            # exception with the return value
            try:
                val=callee(*args, **kwargs)
            except BypassCache, b:
                val=b.value
                now=time()
                return CacheEntry(val,
                                  created=now,
                                  retrieved=now,
                                  expiration=now)
            
            # the callee has a chance to determine the expiration by
            # sending it out of band, through an "expiration"
            # attribute.  otherwise, value passed to this method will
            # be used.
            
            now=time()
            expiration=getattr(callee, 'expiration', expiration) or 0
            if expiration:
                expiration=time_convert(expiration)
            entry=CacheEntry(val,
                             created=now,
                             retrieved=now,
                             expiration=expiration)
            

                
        else:
            raise NotInCache, (callee, callargs)

        if policy.store:
            self._store(entry, cn, ck)
        return entry

    def validateCallable(self, callee, canonicalName=None):
        """
        This verifies that the callable has not changed since the
        cache last dealt with it.  The canonical name is taken to be
        the primary identifier; if the callee's id, hash,
        __lastmodified__ and __file__ attributes (if they exist) have
        changed, that is taken to be an indicator that the code has
        been reloaded, in which case the cache entries for the
        canonical name are invalidated. 
        """
        if canonicalName is None:
            canonicalName=self.getCanonicalName(callee)
        i=id(callee)
        h=hash(callee)
        try:
            d=callee.__lastmodified__
        except AttributeError:
            d=None
        try:
            f=callee.__file__
        except AttributeError:
            
            try:
                m=callee.__module__
            except AttributeError:
                f=None
            else:
                try:
                    f=sys.modules[m].__file__
                except (KeyError, AttributeError):
                    # give up
                    f=None
        try:
            rec=_callable_lookup[canonicalName]
        except KeyError:
            _lookup_lock.acquire()
            try:
                _callable_lookup[canonicalName]=(i, h, d, f)
            finally:
                _lookup_lock.release()
        else:
            if (i, h, d, f)!=rec:
                # invalidate cache for this canonicalName
                self.invalidate(canonicalName)
                _lookup_lock.acquire()
                try:
                    _callable_lookup[canonicalName]=(i, h, d, f)
                finally:
                    _lookup_lock.release()
        
    def invalidate(self, canonicalName):
        """
        invalidates all cache entries for the callable with
        the given canonical name; returns nothing.

        subclasses should implement this.  Note that
        invalidation should be fast, because this is called
        during a call to the cache; it may mean "mark for deletion"
        rather than "delete", if the cache is stored on disk
        and not in memory.
        """
        raise NotImplemented

    def getCanonicalName(self, callee):
        """
        returns the canonical name of the callable.
        For Python functions and classes defined in modules,
        this will be [package].module.name.  Other
        objects (for instance, instances of callable classes),
        should define a __cachename__ attribute that will
        uniquely identify the instance.  It should not, however,
        change when the object is reloaded or modified.
        """
        try:
            return callee.__cachename__
        except AttributeError:
            try:
                return '%s.%s' % (callee.__module__, callee.__name__)
            except AttributeError:
                raise UnCacheable, "callee %s must define either __cachename__"\
                      "or both __module__ and __name__"
                

    def getCacheKey(self, callargs, unpack=True):
        if unpack:
            callargs=self._unpack_callargs(callargs)
        try:
            return md5_new(cPickle_dumps(callargs)).hexdigest()
        except PickleError, pe:
            raise UnCacheable, pe[0]
        
    def _retrieve(self, canonicalName, cacheKey):
        """
        low-level cache access method.

        sub-classes should implement this.
        """
        raise NotImplemented

    def _store(self, entry, canonicalName, cacheKey):
        """
        low-level cache mutator method.

        sub-classes should implement this.
        """        
        raise NotImplemented

    def pack(self):
        """
        cleans up the underlying storage for the cache
        """
        pass
        
                 

class CacheEntry(object):
    def __init__(self,
                 value,
                 created=None,
                 retrieved=None,
                 expiration=0,
                 stored=None):
        self.value=value
        self.created=created
        self.retrieved=retrieved
        self.expiration=expiration
        self.stored=stored

__all__=['Cache', 'CacheEntry']        
