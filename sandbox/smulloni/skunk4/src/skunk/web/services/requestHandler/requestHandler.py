from skunk.util.hooks import Hook
from skunk.util.signal_plus import blockTERM, unblockTERM
from skunk.web.config import Configuration, updateConfig

import select
import signal
import socket
import types
import errno

BeginSession=Hook()
InitRequest=Hook()
HandleRequest=Hook()
PostRequest=Hook()
CleanupRequest=Hook()
EndSession=Hook()

RequestFailed=Hook()

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
    
#    # job must be defined, or else die here
#    if not Configuration.jobs:
#        message="No job specified for service on %s:%d, "\
#                 "request cannot be processed!" % (ip, port)
#        error(message)
#        raise RuntimeError, message
    BeginSession(sock, ctxt)


def _processRequest(sock, addr, protocolImpl):
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
                    requestData = protocolImpl.marshalRequest(sock, ctxt)
                    InitRequest(requestData, ctxt)
                    
                except PreemptiveResponse, pr:
                    responseData=protocolImpl.marshalResponse(pr.responseData, ctxt)
                else:
                    rawResponse=HandleRequest(requestData, ctxt)
                    responseData=protocolImpl.marshalResponse(rawResponse, ctxt)
            except:
                try:
                    responseData=protocolImpl.marshalException(ctxt)
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
        timeout=protocolImpl.keepAliveTimeout(ctxt)
        try:
            if (timeout<0) or not _canRead(sock, timeout):
                _endSession(ctxt)
                return
        except socket.error, v:
            if v != errno.ECONNRESET: #ignore conn reset exceptions
                raise
            _endSession(ctxt)
            return

def _canRead(sock, timeout):
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

class DocumentTimeout(Exception):
    pass                
        
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
        self._initPorts()

    def _initPorts(self):
        from SkunkWeb import Server
        info('initializing ports')
        for port in self.ports:
            bits = port.split(':')
            if bits[0] == 'TCP':
                bits[2] = int(bits[2])
            elif bits[0] == 'UNIX':
                if len(bits)>=3:
                    bits[2] = int(bits[2], 8)
            else: raise "unrecognized socket specifier: %s" % port
            Server.addService(tuple(bits), self)
            
    def __call__(self, sock, addr):
        _processRequest(sock, addr, self.protocol)
 
def addRequestHandler(protocol, ports):
    RequestHandler(protocol, ports)


class PreemptiveResponse(Exception):
    def __init__(self, marshalledResponse=None):
        self.responseData=marshalledResponse
