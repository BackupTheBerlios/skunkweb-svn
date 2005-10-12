from policy import YES



class CacheDecorator(object):
    def __init__(self, cache, defaultExpiration='30s', defaultPolicy=YES):
        self.cache=cache
        self.defaultExpiration=defaultExpiration
        self.defaultPolicy=defaultPolicy

    def __call__(self, expiration=None, policy=None):
        if expiration is None:
            def_exp=True
            expiration=self.defaultExpiration
        else:
            def_exp=False
        if policy is None:
            policy=self.defaultPolicy
        def wrapper(fn):
            if hasattr(fn, 'expiration') and def_exp:
                expiration1=fn.expiration
            else:
                expiration1=expiration
            def newfunc(*args, **kwargs):
                policy2=kwargs.pop('cache', policy)
                expiration2=kwargs.pop('expiration', expiration1)
                res=self.cache.call(fn, (args, kwargs), policy2, expiration2)
                return res.value
            newfunc.__doc__=fn.__doc__
            newfunc.__dict__.update(fn.__dict__)
            newfunc.__name__=fn.__name__
            return newfunc
        return wrapper
    
            
        
__all__=['CacheDecorator']
