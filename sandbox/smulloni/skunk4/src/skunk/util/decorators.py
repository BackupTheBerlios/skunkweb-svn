from __future__ import nested_scopes

def _share_metadata(fn, dec):
    dec.__name__=fn.__name__
    dec.__doc__=fn.__doc__
    dec.__dict__.update(fn.__dict__)



def with_lock(lock):
    """decorator that synchronizes on the given lock"""
    def wrapper(fn):
        def newfunc(*args, **kwargs):
            l=lock
            if not hasattr(l, 'acquire'):
                if callable(l):
                    l=l(*args, **kwargs)
                else:
                    raise ValueError, "lock must be either a Lock or a callable that returns a Lock"
            l.acquire()
            try:
                return fn(*args, **kwargs)
            finally:
                l.release()
        _share_metadata(fn, newfunc)
        return newfunc
    return wrapper

    
