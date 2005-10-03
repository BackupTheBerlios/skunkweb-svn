from md5 import new as md5_new
from cPickle import dumps as cPickle_dumps
from cPickle import PickleError
import sys
import time
from skunk.cache.log import debug
from skunk.cache.exceptions import NotInCache, UnCacheable

_callable_lookup={}

class Cache(object):
    """
    abstract base class for cache implementations.
    """
    def call(self,
             callee,
             callargs,
             policy,
             expiration=None,
             deferralQueue=None):
        """
        invokes the callee with callargs through the cache, with the
        given cache policy.  This is the main user-space method.  It
        returns a CacheEntry instance.  The entry will only be
        guaranteed to have storage if policy.store is true.
        """
        # the canonical name and cache key are
        # needed both for retrieve and store;
        # just get them once
        debug("policy is %r", policy)

        if policy.defer and deferralQueue is None:
            raise ValueError, "cannot use cache policy DEFER without a deferral queue"

        if policy.retrieve or policy.store:
            cn=self.getCanonicalName(callee)
            ck=self.getCacheKey(callargs)            
        
        if policy.retrieve:
            # has the callee changed since
            # last checked?
            self.validateCallable(callee, cn)
            
            # get the cache entry if it exists
            entry=self._retrieve(cn, ck)
            if entry and policy.accept(entry):
                entry.retrieved=time.time()
                return entry

        if policy.defer:
            assert deferralQueue is not None
            if entry:
                deferralQueue.append((callee, callargs, expiration))
                return entry
            # else fall through to calculate

        if policy.calculate or policy.defer:
            debug("callargs are %r", callargs)
            val=callee(**callargs)
            # the callee has a chance to determine
            # the expiration by sending it out of band,
            # through an "expiration" attribute.
            # otherwise, value passed to this method will
            # be used.
            expiration=getattr(callee, 'expiration', expiration)
            now=time.time()
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
            _callable_lookup[canonicalName]=(i, h, d, f)
        else:
            if (i, h, d, f)!=rec:
                # invalidate cache for this canonicalName
                self.invalidate(canonicalName)
                _callable_lookup[canonicalName]=(i, h, d, f)
        
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
                

    def getCacheKey(self, callargs):
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
                 

class CacheEntry(object):
    def __init__(self,
                 value,
                 created=None,
                 retrieved=None,
                 expiration=None,
                 stored=None):
        self.value=value
        self.created=created
        self.retrieved=retrieved
        self.expiration=expiration
        self.stored=stored

__all__=['Cache', 'CacheEntry']        
