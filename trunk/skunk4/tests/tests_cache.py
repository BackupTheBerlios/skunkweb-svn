import os
import sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src')))
import skunk.cache as C
import time
import tempfile
import unittest
import shutil

def dullfunc(*args, **kwargs):
    return time.time()

def bypassfunc():
    raise C.BypassCache, time.time()

class CacheTestCase(unittest.TestCase):

    def setUp(self):
        self.diskcache=C.DiskCache(os.path.join(tempfile.gettempdir(), 'testcache'))
        self.memcache=C.MemoryCache()
        
    def tearDown(self):
        shutil.rmtree(self.diskcache.path)

    def test_unexpired(self):
        for c in self.diskcache, self.memcache:
            entry1=c.call(time.asctime, {}, policy=C.YES, expiration=time.time()+2)
            time.sleep(0.1)
            entry2=c.call(time.asctime, {}, policy=C.YES, expiration=time.time()+2)
            assert entry1.value==entry2.value
            assert entry1.created==entry2.created
            assert entry1.retrieved <= entry2.retrieved

    def test_expire1(self):
        for c in self.diskcache, self.memcache:
            e1=c.call(time.time, None, C.YES, expiration="2s")
            e2=c.call(time.time, None, C.YES, expiration="2s")
            time.sleep(2)
            e3=c.call(time.time, None, C.YES, expiration="2s")
            assert e1.value==e2.value
            assert e3.value > e1.value

    def test_force1(self):
        for c in self.diskcache, self.memcache:
            callargs=((4, 5, 6), dict(x='nougat', y='chunk'))
            e1=c.call(dullfunc, callargs, C.YES, expiration="10m")
            e2=c.call(dullfunc, callargs, C.YES, expiration="10m")
            time.sleep(0.1)
            e3=c.call(dullfunc, callargs, C.FORCE, expiration="10m")
            assert e1.value==e2.value
            assert e3.value > e1.value
            
    def test_invalidate(self):
        for c in self.diskcache, self.memcache:
            e1=c.call(time.time, None, C.YES, expiration="24h")
            c.invalidate('time.time')
            time.sleep(0.1)
            e2=c.call(time.time, None, C.YES, expiration="1s")
            assert e2.value > e1.value

    def test_bypass(self):
        for c in self.diskcache, self.memcache:
            e1=c.call(bypassfunc, None, C.YES, expiration="30m")
            time.sleep(0.1)
            e2=c.call(bypassfunc, None, C.YES, expiration="30m")
            assert e2.value > e1.value

            
if __name__=='__main__':
    unittest.main()
    
    
        
