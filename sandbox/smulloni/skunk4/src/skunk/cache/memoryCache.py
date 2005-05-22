from skunk.cache.base import Cache
import time

class MemoryCache(Cache):
    def __init__(self):
        self._d={}

    def _retrieve(self, canonicalName, cacheKey):
        try:
            e=self._d[canonicalName][cacheKey]
        except KeyError:
            return None
        else:
            return e


    def _store(self, entry, canonicalName, cacheKey):
        entry.stored=time.time()
        try:
            self._d[canonicalName][cacheKey]=entry
        except KeyError:
            self._d[canonicalName]={cacheKey : entry}
                 


    def invalidate(self, canonicalName): 
        try:
            del self._d[canonicalName]
        except KeyError:
            pass


__all__=['MemoryCache']

    
