
class CacheException(Exception):
    pass

class NotInCache(CacheException):
    pass

class UnCacheable(CacheException):
    pass

class BypassCache(Exception):
    def value():
        def fget(self):
            if self.args:
                return self.args[0]
        return fget
    value=property(value())
    
class NotImplementedWarning(Warning):
    pass
