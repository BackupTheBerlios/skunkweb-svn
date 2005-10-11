import os
import sys
sys.path.append(os.path.abspath(os.path.join(__file__, '../../src')))
import skunk.cache as C
import time
import tempfile
import unittest
import shutil

def testfunc(x, y, z):
    return dict(stuff=[x, y, z, time.time()])

class CacheTestCase(unittest.TestCase):

    def setUp(self):
        self.caches=(C.DiskCache(os.path.join(tempfile.gettempdir(), 'testcache')),
                     C.MemoryCache())

    def tearDown(self):
        for c in self.caches:
            if hasattr(c, 'path'):
                shutil.rmtree(c.path)

    def test_unexpired(self):
        for c in self.caches:
            entry1=c.call(time.asctime, {}, policy=C.YES, expiration=time.time()+2)
            time.sleep(0.1)
            entry2=c.call(time.asctime, {}, policy=C.YES, expiration=time.time()+2)
            assert entry1.value==entry2.value
            assert entry1.created==entry2.created
            assert entry1.retrieved <= entry2.retrieved


        
if __name__=='__main__':
    unittest.main()
    
    
        
