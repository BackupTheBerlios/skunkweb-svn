
from skunk.net.server.processmgr import ProcessManager

import fcntl
from select import select
import socket
import errno
import sys
import os
import platform
import stat
import time

def _serialize_accept():
    system=platform.system()
    version=platform.release()
    if system=='Linux':
        return  version <'2.2'
    # most unices support this now, so the default is False.
    # add more exceptions  -- TBD
    return False
    

class SocketManager(ProcessManager):
    def __init__(self,
                 numProcs,
                 pidFile,
                 maxKillTime=5,
                 pollPeriod=5,
                 logger=None,
                 foreground=False,
                 maxRequests=None):
        self.maxRequests = maxRequests
        self.socketMap = {}
        ProcessManager.__init__(self,
                                numProcs=numProcs,
                                pidFile=pidFile,
                                maxKillTime=maxKillTime,
                                pollPeriod=pollPeriod,
                                logger=logger,
                                foreground=foreground)

    def preHandle(self):
        pass

    def postHandle(self):
        pass
    
    def _run(self):
        connectionCount = 0
        info=self.info
        exception=self.exception

        # this shouldn't change in the child process!
        socks=self.socketMap.keys()
        lensocks=len(socks)
        if not lensocks:
            return
        # no need to select if there is only one, just block on accept
        doselect=lensocks>1
        if doselect:
            # don't lock on a single process
            dolocking=self.numProcs>1
        else:
            # blocking on accept, lock only if the OS has a thundering herd
            # problem and there are multiple processes
            dolocking=_serialize_accept() and self.numProcs>1
        if dolocking:
            lockfile=open(self.pidFile)
            lfd=lockfile.fileno()
        
        while 1:
            connectionCount += 1
            if self.maxRequests and connectionCount > self.maxRequests:
                info('hit maxRequests %d, recycling', self.maxRequests)
                break
            have_connection = 0
            while not have_connection:

                if dolocking:
                    # serialize both select and accept, together
                    fcntl.flock(lfd, fcntl.LOCK_EX)
                try:
                    if doselect:
                        try:
                            r,w,e = select(socks, [], [])
                        except:
                            # this should only happen if errno is EINTR, but
                            # exiting is still probably the best idea here
                            exception('select failed! socket list is %s', socks)
                            break

                        s = r[0]
                    else:
                        s=socks[0]
                    try:
                        sock, addr = s.accept()
                        sock.setblocking(1)
                    except socket.error, (err, errstr):
                        if err not in (errno.EAGAIN, errno.EWOULDBLOCK):
                            exception("socket error!")
                            raise
                    else:
                        have_connection = 1
                finally:
                    if dolocking:
                        fcntl.flock(lfd, fcntl.LOCK_UN)
            if not have_connection:
                self.warn('exiting due to no connection')
                break 
            
            r = None
            try:
                try:
                    self.preHandle()
                except:
                    exception('preHandle died: ')

                r = self.socketMap[s][0](sock, addr)
                try:
                    self.postHandle()
                except:
                    exception('postHandle died: ')

            except:
                exception("handler %s died: ",
                          self.socketMap[s][0])
            sock.close()
            if r:
                info('socket manager exiting due to return value from handler being true') 
                break
                
    def run(self):
        try:
            self._run()
        except:
            self.exception("BUG!")
            raise
        
    def reload(self):
        super(SocketManager, self).reload()
        self._reset()

    def retrying_bind(self, sock, addr, retries):
        # mayhap it's not quite dead, so retry a few times
        retrycount = retries 
        while retrycount:
            try:
                sock.bind(addr)
            except:
                retrycount = retrycount - 1
                if retrycount == 0:
                    raise
                time.sleep(1)
            else:
                break
        
    def addConnection(self, addrspec, handler_func):
        if addrspec[0] == 'TCP':
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #s.setblocking(0)
            s.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Make sure the socket will be closed on exec
            fcntl.fcntl (s.fileno(), fcntl.F_SETFD, 1)
            self.retrying_bind(s, tuple(addrspec[1:]), 5)
            s.listen(5)
        elif addrspec[0] == 'UNIX':
            try:
                pathstat=os.stat(addrspec[1])
            except OSError:
                pathstat=None
            if pathstat:
                # oops, file exists; is it a UNIX socket?
                if stat.S_ISSOCK(pathstat[0]):
                    # yes, delete it and start over;
                    # let any exception propagate
                    os.unlink(addrspec[1])
                else:
                    # if you've got something else there,
                    # I'm not going to delete it.
                    raise IOError, \
                          "file exists where unix "\
                          "socket is to be created: %s" % addrspec[1]
                    
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            #s.setblocking(0)
            # Make sure the socket will be closed on exec
            fcntl.fcntl(s.fileno(), fcntl.F_SETFD, 1)
            self.retrying_bind(s, addrspec[1], 5)
                    
            if len(addrspec) == 3:
                os.chmod(addrspec[1], addrspec[2])
            s.listen(5)
        else:
            raise ValueError, "unknown bind address type"
        self.socketMap[s] = handler_func, addrspec
        # if there is only one socket, set it to be blocking, as we
        # won't be using select.  Otherwise, set all sockets not to
        # block.
        block=len(self.socketMap)==1        
        for sock in self.socketMap:
            sock.setblocking(block)
        
            
    def stop(self):
        self._reset()

    def _reset(self):
        for k, (f, a) in self.socketMap.iteritems():
            k.close()
            if a[0] == 'UNIX':
                try:
                    os.remove(a[1])
                except:
                    self.error(('removal of unix socket %s '
                                'failed, continuing and hoping'
                                ' for the best') % a[1])

        self.socketMap = {}




