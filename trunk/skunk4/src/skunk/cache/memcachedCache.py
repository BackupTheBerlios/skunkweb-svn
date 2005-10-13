"""

This cache currently does not support invalidation of cache entries by
canonicalName, as memcached does not support partitioning the cache
into sub-caches, or indexing the cache entries.

A fairly expensive workaround is possible:creating a sequence in
memcached for each canonicalName and adding to the key, and
incrementing the sequence to invalidate that partition of the cache.
This would mean that every cache hit would require at the very least a
retrieval of the sequence.  That invalidation wouldn't actually free
memory isn't as important.

"""

import memcache
from skunk.cache.base import Cache
from skunk.cache.log import error
from skunk.cache.exceptions import NotImplementedWarning
from time import time


import warnings

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
        """
        not implemented, but sends a warning, rather than an error.
        """
        warnings.warn("cache invalidation is not currently supported by the memcached backend",
                      NotImplementedWarning)

        

            
