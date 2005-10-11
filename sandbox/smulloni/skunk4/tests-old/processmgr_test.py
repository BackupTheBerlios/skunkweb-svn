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
    logger=logging.getLogger('skunk.net.server')
    logging.basicConfig()
    logger.setLevel(logging.INFO)
    tempname='/tmp/processmgr_test_%d.pid' % os.getpid()
    mgr=TestProcessManager(numProcs=3, pidFile=tempname)
    kid=os.fork()
    if kid:
        mgr.mainloop()
    else:
        time.sleep(3)
        pid=int(open(tempname).read())
        os.kill(pid, signal.SIGHUP)
        time.sleep(3)
        os.kill(pid, signal.SIGTERM)

            
if __name__=='__main__':
    test1()

