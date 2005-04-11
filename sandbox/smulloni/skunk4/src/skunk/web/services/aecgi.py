from skunk.web.config import Configuration, mergeDefaults
from skunk.web.services.requestHandler import (Protocol,
                                               RequestFailed,
                                               addRequestHandler)
from skunk.net.SocketScience import read_this_many
from skunk.util.logutil import loginit
import marshal

# log methods
loginit(make_all=False)

class AecgiProtocol(Protocol):
    """
    protocol used to communicate with Apache via mod_skunkweb
    """
    
    def marshalRequest(self, sock, ctxt):
        """
        Sends a handshake byte, obtains the content length from
        the value of the first ten bytes read, and then reads no
        more than that amount, which it marshals with the 'marshal'
        module. Finally, returns the marshalled request data
        """
        sock.sendall('\0')
        debug('sent sentinel')
        lenDataStr = read_this_many(sock, 10)
        debug('read length')
        lenData = int(lenDataStr)
        data = read_this_many(sock, lenData)
        debug('read request data')
        return marshal.loads(data)

    def marshalResponse(self, response, ctxt):
        """return response data, with the first ten bytes indicating
        the content length.
        """
        return self._marshalData(response)

    def marshalException(self, ctxt, exc_info=None):
        """should return response data appropriate for the current exception.
        """
        if exc_info is None:
            exc_info=sys.exc_info()
        res=RequestFailed(ctxt, exc_info)

        if res:
            return self._marshalData(res)
        else:
            exc_text=''.join(format_exception(*exc_info))
            return self._marshalData(exc_text)

    def _marshalData(self, data):
        return "%10d%s" %(len(data), data)

def serviceInit():
    """service initialization function"""
    if Configuration.AecgiListenPorts:
        addRequestHandler(AecgiProtocol(),
                          Configuration.AecgiListenPorts)    

mergeDefaults(AecgiListenPorts=['TCP:localhost:9888'])



