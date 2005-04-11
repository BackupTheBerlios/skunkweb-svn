from skunk.util.hooks import Hook
from skunk.util.logutil import loginit
from skunk.util.signal_plus import blockTERM, unblockTERM
from skunk.web.config import (Configuration, updateConfig,
                              _scopeman, mergeDefaults)

import select
import signal
import socket
import errno

# create standard logging methods
loginit(make_all=False)

__all__=['BeginSession',
         'InitRequest',
         'HandleRequest',
         'PostRequest',
         'CleanupRequest',
         'EndSession',
         'RequestFailed',
         'addRequestHandler',
         'PreemptiveResponse',
         'DocumentTimeout',
         'Protocol']

mergeDefaults(DocumentTimeout=30,
              PostResponseTimeout=20,
              jobs=())

# hooks
BeginSession=Hook()
InitRequest=Hook()
HandleRequest=Hook()
PostRequest=Hook()
CleanupRequest=Hook()
EndSession=Hook()
RequestFailed=Hook()

def processRequest(sock, addr, protocol):
    """ the actual handler for requestHandler-managed requests."""
    requestData, responseData, ctxt=None, None, {}
    _beginSession(sock, ctxt)
    
    # loop until connection is closed
    while 1:
        try:
            blockTERM()
            signal.signal(signal.SIGALRM, SIGALRMHandler)
            signal.alarm(Configuration.DocumentTimeout)
            try:
                try:
                    requestData = protocol.marshalRequest(sock, ctxt)
                    InitRequest(requestData, ctxt)
                    
                except PreemptiveResponse, pr:
                    responseData=protocol.marshalResponse(pr.responseData, ctxt)
                else:
                    rawResponse=HandleRequest(requestData, ctxt)
                    responseData=protocol.marshalResponse(rawResponse, ctxt)
            except:
                try:
                    responseData=protocol.marshalException(ctxt)
                except:
                    exception("exception in marshalling exception!") 
            try:
                _sendResponse(sock, responseData, requestData, ctxt)
            except:
                exception('error sending response')
        finally:
            signal.alarm(0)
            unblockTERM()

        # the protocol can close the connection by return a negative timeout;
        # ctxt allows it to reference state that has been stored there.
        timeout=protocol.keepAliveTimeout(ctxt)
        try:
            if (timeout<0) or not _canRead(sock, timeout):
                _endSession(ctxt)
                return
        except socket.error, v:
            if v != errno.ECONNRESET: #ignore conn reset exceptions
                raise
            _endSession(ctxt)
            return

def _beginSession(sock, ctxt):
    # capture the ip & port (or path, for a unix socket)
    # on which the request came, for scoping of configuration
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
    
    # get configuration data for the job
    updateConfig(ctxt)
    BeginSession(sock, ctxt)

def _canRead(sock, timeout):
    """peeks at the socket to see if it can actually be read."""
    sock.setblocking(1)
    input, output, exc=select.select([sock],
                                     [],
                                     [],
                                     timeout)
    # sanity check
    try:
        if input and not input[0].recv(1, socket.MSG_PEEK):
            return 0
    except socket.error:
        return 0

    return len(input)

def SIGALRMHandler(*args):
    updateConfig()
    error('Throwing timeout exception')
    signal.alarm(1) # in case they catch this exception
    raise DocumentTimeout, "timeout reached"

def _sendResponse(sock,
                  responseData,                 
                  requestData,
                  ctxt):
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
        PostRequest(requestData, ctxt)
    except:
        exception("error in PostRequest")
    try:
        CleanupRequest(requestData, ctxt)
    except:
        exception("error in CleanupRequest")


def _endSession(ctxt):
    try:
        EndSession(ctxt)
    except:
        exception("error in EndSession")
    updateConfig()

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

class PreemptiveResponse(Exception):
    def __init__(self, marshalledResponse=None):
        self.responseData=marshalledResponse

class DocumentTimeout(Exception):
    pass                


class Protocol(object):
    """
    interface for protocols used in handling request and response.
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

        

