import os
import logging
import signal
import sys
import time

sys.path.append('../src')

from skunk.net.server.socketmgr import SocketManager


def test1():
    logger=logging.getLogger()
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    tempname='/tmp/socketmgr_test.pid'
    mgr=SocketManager(2, tempname, logger=logger, maxRequests=30)
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
    mgr.addConnection(('TCP', 'localhost', 8888), handler)
    mgr.mainloop()
        
        
if __name__=='__main__':
    test1()
        
                      
                      
