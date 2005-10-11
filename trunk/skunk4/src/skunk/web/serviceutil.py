from skunk.web.config import Configuration
from skunk.util.decorators import _share_metadata

def matchJobs(*jobs):
    """decorator for hook functions that should only execute depending on certain
    values being in Configuration.jobs"""
    def wrapper(fn):
        def newfunc(*args, **kwargs):
            confjobs=set(Configuration.jobs)
            if confjobs.issuperset(jobs):
                return fn(*args, **kwargs)
        _share_metadata(fn, newfunc)
        return newfunc
    return wrapper


__all__=['matchJobs']    
