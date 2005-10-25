Using the ``skunk.cache`` 
~~~~~~~~~~~~~~~~~~~~~~~~~

Synopsis
========

The ``skunk.cache`` package provides a flexible memoization
cache. Example use::

  from skunk.cache import *
  import time

  cache=CacheDecorator(DiskCache('/tmp/mycache'),
                                 defaultPolicy=YES)

  @cache('5m')
  def foobar():
      return time.time()

The value returned by a call to ``foobar`` will be cached for five
minutes::

  t1=foobar()
  t2=foobar()
  assert t1==t2

You can call the cache with a different cache policy::

  t3=foobar(cache=FORCE)
  assert t3 > t2

Cache Policies
==============

To Be Done.

Cache Backends
==============

There are currently three cache backends -- a memory cache, a disk
cache, and a memcached cache.


  

  



  




  

