import os
import logging
import signal
import sys
import time

sys.path.append('../src')

from skunk.net.server.socketmgr import SocketManager
from skunk.net.server.log import logger


def test1():
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    tempname='/tmp/socketmgr_test.pid'

    def handler(socket, addr):
        logger.info("addr is %s", addr)
        # read some off the socket
        while 1:
            stuff=socket.recv(1024)
            stuff=stuff.strip()
            if not stuff:
                continue
            if stuff=='quit':
                socket.send('bye\n')
                socket.close()
                break
            socket.send('%s\n' % stuff.upper())
    mgr=SocketManager(tempname, numProcs=2, maxRequests=30,
                      connections={('TCP', 'localhost', 8888): handler})            
    mgr.mainloop()
        
        
if __name__=='__main__':
    if len(sys.argv)>1:
        try:
            pid=int(open('/tmp/socketmgr_test.pid').read())
        except:
            print >> sys.stderr, "couldn't read pid file!"
            sys.exit(1)
        else:
            if sys.argv[1]=='TERM':
                os.kill(pid, signal.SIGTERM)
            elif sys.argv[1]=='HUP':
                os.kill(pid, signal.SIGHUP)
            sys.exit(0)
    else:
        test1()
        
                      
                      
