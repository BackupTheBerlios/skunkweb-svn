"""

This module supplies a class, CacheDecorator, instances of which can
be used as decorators that cache the return value of the wrapped
function.  The cache policy and expiration can be set in the
decorator, and also may be overridden when the function is called with
the keyword arguments "cache" (for policy) and "expiration".

Issues:

   * the resulting function seems to have the wrong __module__ attribute.
   * the function signature is genericized; it would nice to have it
     be the same as the original function, plus the two additional optional
     parameters.
   * If the two additional parameters conflict with the original signature,
     that would be a Bad Thing.

Example usage:

  >>> from skunk.cache import MemoryCache, CacheDecorator, YES, FORCE
  >>> cache=CacheDecorator(MemoryCache())
  >>> import time
  >>> @cache(expiration="30s")
  ... def timestamp():
          return time.time()
  >>> x=timestamp()
  >>> y=timestamp()
  >>> x==y
  True
  >>> z=timestamp(cache=FORCE)
  >>> x<z
  True

"""


from policy import YES


_default=object()

class CacheDecorator(object):
    def __init__(self, cache, defaultExpiration='30s', defaultPolicy=YES, defaultOndefer=None):
        self.cache=cache
        self.defaultExpiration=defaultExpiration
        self.defaultPolicy=defaultPolicy
        self.defaultOndefer=defaultOndefer

    def __call__(self, expiration=None, policy=None, ondefer=_default):
        if expiration is None:
            def_exp=True
            expiration=self.defaultExpiration
        else:
            def_exp=False
        if policy is None:
            policy=self.defaultPolicy
        if ondefer is _default:
            ondefer=self.defaultOndefer
        # workaround for nested scope bug/wart -- you can't assign to
        # variables in intermediate (not global, not local) scopes
        def wrapper(fn):
            if hasattr(fn, 'expiration') and def_exp:
                expiration1=fn.expiration
            else:
                expiration1=expiration
            def newfunc(*args, **kwargs):
                policy2=kwargs.pop('cache', policy)
                expiration2=kwargs.pop('expiration', expiration1)
                ondefer2=kwargs.pop('ondefer', ondefer)
                res=self.cache.call(fn, (args, kwargs), policy2, expiration2, ondefer2)
                return res.value
            if hasattr(fn, '__doc__'):
                newfunc.__doc__=fn.__doc__
            if hasattr(fn, "__dict__"):
                newfunc.__dict__.update(fn.__dict__)
            if hasattr(fn, '__name__'):
                newfunc.__name__=fn.__name__
            return newfunc
        return wrapper
    
__all__=['CacheDecorator']
