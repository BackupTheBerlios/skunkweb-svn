def simple_decorator(decorator):
    """
    This decorator can be used to turn simple functions into
    well-behaved decorators, so long as the decorators are fairly
    simple. If a decorator expects a function and returns a function
    (no descriptors), and if it doesn't modify function attributes or
    docstring, then it is eligible to use this. Simply apply
    @simple_decorator to your decorator and it will automatically
    preserve the docstring and function attributes of functions to
    which it is applied.

    This was adapted from an example in the Python decorator library
    on the Python wiki:
    
    http://www.python.org/moin/PythonDecoratorLibrary

    Unfortunately, neither it nor the original work at the moment....
    """
    def new_decorator(f):
        g = decorator(f)
        for attr in ('__name__', '__doc__'):
            if hasattr(f, attr):
                setattr(g, attr, getattr(f, attr))
        if hasattr(f, '__dict__') and hasattr(g, "__dict__"):
            g.__dict__.update(f.__dict__)
        return g
    return new_decorator(new_decorator)


#@simple_decorator
def with_lock(lock):
    def wrapper(fn):
        def newfunc(*args, **kwargs):
            lock.acquire()
            try:
                return fn(*args, **kwargs)
            finally:
                lock.release()
        return newfunc
    return wrapper
    
