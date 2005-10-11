class _oneshot(object):
    def __init__(self, hook, func):
        self.hook=hook
        self.func=func

    def __call__(self, *args, **kwargs):
        try:
            self.func(*args, **kwargs)
        finally:
            self.hook.remove(self)

class Hook(list):
    """a hook function"""
    def __call__(self, *args, **kw):
        for i in self:
            ret = i(*args, **kw)
            if ret is not None:
                return ret
            
    def oneshot(self, func, index=None):
        """add a function to the hook which will only get called once
        and then will remove itself from the hook"""
        if not index:
            index=len(self)
        self.insert(index, _oneshot(self, func))


