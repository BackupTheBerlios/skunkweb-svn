import memcache
from skunk.cache.base import Cache
from time import time
from log import error

class MemcachedCache(Cache):
    def __init__(self, servers, debug=0):
        self._client=memcache.Client(servers, debug=debug)

    def _get_key(self, canonicalName, cacheKey):
        t=(canonicalName, cacheKey)
        return "%s---%s" % t

    def _retrieve(self, canonicalName, cacheKey):
        return self._client.get(self._get_key(canonicalName, cacheKey))

    def _store(self, entry, canonicalName, cacheKey):
        now=time()
        entry.stored=now
        expiration=max(now, entry.expiration)-now
        res=self._client.set(self._get_key(canonicalName, cacheKey), entry, expiration)
        if not res:
            error("couldn't store entry!")
        
    def invalidate(self, canonicalName):
        # should I raise an error?  flush all the entries?
        pass

            
