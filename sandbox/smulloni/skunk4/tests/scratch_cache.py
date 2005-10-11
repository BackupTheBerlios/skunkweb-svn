import sys, os
sys.path.append(os.path.abspath('../src'))
import skunk.cache as C
import random
import time


cache=C.DiskCache('/home/smulloni/testcache')


def foo(x, y):
    print "executing at %s" % time.asctime()
    return time.time()

## for i in range(2):
##     entry=cache.call(foo, dict(x=5, y=6), expiration=time.time()+2, policy=C.policy.YES)
##     print entry.value
##     time.sleep(1)


## for i in range(2):
##     entry=cache.call(foo, dict(x=5, y=6), expiration=time.time()+1, policy=C.policy.YES)
##     print entry.value
##     time.sleep(1)


## for i in range(2):
##     entry=cache.call(foo, dict(x=5, y=6), expiration=None, policy=C.policy.YES)
##     print entry.value
##     time.sleep(1)

## for i in range(3):
##     entry=cache.call(foo, dict(x=5, y=6), expiration=time.time()+10, policy=C.policy.YES)
##     print entry.value
##     time.sleep(1)

## print "does policy accept with expiration None? : ", C.policy.YES.accept(entry, None)
## print "with expiration currentTime? : ", C.policy.YES.accept(entry, time.time())
## entry=cache.call(foo, dict(x=5, y=6), policy=C.policy.FORCE)
## print "does policy accept with expiration None? : ", C.policy.YES.accept(entry, None)
## print "with expiration currentTime? : ", C.policy.YES.accept(entry, time.time())

def cachecall(func, **kwargs):
    expiration=kwargs.pop('expiration', time.time()+30)
    policy=C.policy.decode(kwargs.pop('cache', 'YES'))
    entry=cache.call(func, kwargs, expiration=expiration, policy=policy)
    return entry.value
