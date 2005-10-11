import logging
import os
import signal
import sys
import time

sys.path.append('../src')

from skunk.net.server.processmgr import ProcessManager

class TestProcessManager(ProcessManager):
    def run(self):
        self.info("%d in run()", os.getpid())
        while 1:
            time.sleep(50)



def test1():
    logger=logging.getLogger()
    logging.basicConfig()
    logger.setLevel(logging.INFO)
    pidfile='/tmp/processmgr_test.pid'
    mgr=TestProcessManager(numProcs=3, pidFile=pidfile, logger=logger)
    mgr.mainloop()
            
if __name__=='__main__':
    test1()

