"""
Cache policies here control these factors when accessing a
cache-enabled function:

  * whether or not to retrieve values from the cache.  Possibilities
    are: never to retrieve from the cache, to retrieve based on cache
    entry expiration, or to always retrieve.

  * whether or not to calculate the memoized function if no cache
    entry is retrieved.

  * whether or not to store any calculated value in the cache.

"""

from time import time

RETRIEVE_NEVER=0
RETRIEVE_UNEXPIRED=1
RETRIEVE_ALWAYS=2

class CachePolicy(object):

    def __init__(self,
                 retrieve,
                 calculate,
                 store,
                 defer=False):
        # should be one of the RETRIEVE constants
        self.retrieve=retrieve
        # should be boolean
        self.calculate=calculate
        # ditto
        self.store=store
        self.defer=defer

    def accept(self, cacheEntry, expiration=None):
        if self.retrieve==RETRIEVE_UNEXPIRED:
            if expiration:
                e=max(cacheEntry.expiration, expiration)
            else:
                e=cacheEntry.expiration
            return e > time()
        else:
            return self.retrieve==RETRIEVE_ALWAYS

        
NO=CachePolicy(RETRIEVE_NEVER,
               True,
               False)

YES=CachePolicy(RETRIEVE_UNEXPIRED,
                True,
                True)

OLD=CachePolicy(RETRIEVE_ALWAYS,
                False,
                True)

FORCE=CachePolicy(RETRIEVE_NEVER,
                  True,
                  True)

DEFER=CachePolicy(RETRIEVE_ALWAYS,
                  True,
                  True,
                  True)

# for AE's DEFER, you'd use an OLD, and then, depending on whether the
# returned value was calculated and stored or not, a FORCE later. So
# we need to know the status of store, at least.

_codes={'yes'   : YES,
        'no'    : NO,
        'force' : FORCE,
        'old'   : OLD,
        'defer' : DEFER,
        1       : YES,
        0       : NO,
        True    : YES,
        False   : NO,
        None    : NO}

def decode(key):
    if isinstance(key, CachePolicy):
        return key
    try:
        key=key.lower()
    except AttributeError:
        pass
    try:
        return _codes[key]
    except KeyError:
        raise ValueError, "unrecognized cache policy"
    

__all__=['RETRIEVE_NEVER',
         'RETRIEVE_UNEXPIRED',
         'RETRIEVE_ALWAYS',
         'NO',
         'YES',
         'OLD',
         'FORCE',
         'DEFER',
         'CachePolicy',
         'decode']
