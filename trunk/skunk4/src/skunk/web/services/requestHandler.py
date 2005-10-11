"""

This service splits request handling into two parts:

  1. a client protocol.  This is a translation layer responsible for
     performing actual communication with the client, and also control
     whether connections should be kept alive.
  2. a hook for jobs to handle requests.


"""

from skunk.net.SocketScience import can_read
from skunk.util.hooks import Hook
from skunk.util.logutil import loginit
from skunk.util.signal_plus import blockTERM, unblockTERM
from skunk.web.config import (Configuration, updateConfig,
                              _scopeman, mergeDefaults)

import signal
import socket
import errno

# create standard logging methods
loginit(make_all=False)

__all__=['HandleRequest',
         'PostResponse',
         'RequestFailed',
         'addRequestHandler',
         'DocumentTimeout',
         'ClientProtocol']

mergeDefaults(DocumentTimeout=30,
              PostResponseTimeout=20,
              jobs=())

# hooks
HandleRequest=Hook()
PostResponse=Hook()


def processRequest(sock, addr, protocol):
    """ the actual handler for requestHandler-managed requests."""
    requestData, responseData, ctxt=None, None, {}
    # capture the socket address (ip & port, or path, for a unix
    # socket) on which the request came, for scoping of configuration
    # data on their basis
    ip, port, unixpath=None, None, None
    try:      
        addr=sock.getsockname()
        if isinstance(addr, tuple):
            ip, port=addr
        else:
            unixpath=addr
    except:
        exception("failed to read addr off socket!")
        raise

    if ip and port:
        ctxt['IP']=ip
        ctxt['PORT']=port
    else:
        ctxt['UNIX_SOCKET_PATH']=unixpath
    
    # load configuration data for the job
    updateConfig(ctxt)
    
    # loop until connection is closed
    while 1:
        try:
            blockTERM()
            signal.signal(signal.SIGALRM, SIGALRMHandler)
            signal.alarm(Configuration.DocumentTimeout)
            try:
                rawResponse=HandleRequest(requestData, ctxt)
                responseData=protocol.marshalResponse(rawResponse, ctxt)
            except:
                try:
                    responseData=protocol.marshalException(ctxt)
                except:
                    exception("ironic exception in marshalling exception!")
                    raise
            try:
                sock.sendall(responseData)
            except IOError, en:
                # ignore broken pipes
                if en != errno.EPIPE:
                    exception("IO error")
            except:
                exception("error sending response")
 
            # reset alarm
            signal.alarm(Configuration.PostResponseTimeout)
    
            try:
                PostResponse(requestData, ctxt)
            except:
                exception("error in PostResponse")

        finally:
            signal.alarm(0)
            unblockTERM()
            
        timeout=protocol.keepAliveTimeout(ctxt)
        ending=timeout<0
        if not ending:
            try:
                ending=not can_read(sock, timeout)
            except socket.error, e:
                ending=1
                if not e.args or e.args[0] != errno.ECONNRESET:
                    exception('problem with socket, ending connection')
            except:
                ending=1
                exception("problem testing socket")

        if ending:
            updateConfig()
            return

def SIGALRMHandler(*args):
    updateConfig()
    error('Throwing timeout exception')
    # in case this exception is caught, raise another in one second
    signal.alarm(1) 
    raise DocumentTimeout, "timeout reached"


class RequestHandler(object):
    """
    an object, the creation of which adds a service
    to the server on the specified ports with the specified
    protocol.
    """
    def __init__(self, protocol, ports):
        self.protocol=protocol
        self.ports=ports
        info('initializing ports')
        conns=[]
        for port in ports:
            bits = port.split(':')
            if bits[0] == 'TCP':
                bits[2] = int(bits[2])
            elif bits[0] == 'UNIX':
                if len(bits)>=3:
                    bits[2] = int(bits[2], 8)
            else: raise ValueError, "unrecognized socket specifier: %s" % port
            conns.append(tuple(bits))
        _scopeman.lock.acquire()
        try:
            _scopeman.defaults.setdefault('connections', {})
            curconns=_scopeman.defaults['connections']
            for c in conns:
                curconns[c]=self
        finally:
            _scopeman.lock.release()

    def __call__(self, sock, addr):
        processRequest(sock, addr, self.protocol)
 
addRequestHandler=RequestHandler

class DocumentTimeout(Exception):
    pass                

RequestFailed=Hook()
RequestFailed.__doc__="""\
A hook function that may be used by ClientProtocol implementations in marshalException().
"""

class ClientProtocol(object):
    """
    interface for protocols used in handling request and response.
    This is the communication protocol for communicating with the
    (immediate) client.
    """

    def marshalRequest(self, socket, ctxt):
        '''
        should return the marshalled request data
        '''
        raise NotImplementedError

    def marshalResponse(self, response, ctxt):
        '''
        should return response data
        '''
        raise NotImplementedError

    def marshalException(self, ctxt, exc_info=None):
        '''
        should return response data appropriate for the current exception.
        '''
        raise NotImplementedError

    def keepAliveTimeout(self, ctxt):
        '''
        how long to keep alive a session.  A negative number will terminate the
        session.
        '''
        return -1

        


