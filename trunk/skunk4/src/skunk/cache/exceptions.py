
class CacheException(Exception):
    pass

class NotInCache(CacheException):
    pass

class UnCacheable(CacheException):
    pass
