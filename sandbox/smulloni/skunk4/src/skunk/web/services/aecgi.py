
from skunk.web.config import Configuration

import requestHandler.protocol
import requestHandler.requestHandler
from requestHandler.protocol import RequestFailed
from skunk.net.SocketScience import read_this_many

import marshal


class AecgiProtocol(requestHandler.protocol.Protocol):
    """
    protocol used to communicate with Apache via mod_skunkweb
    """
    
    def marshalRequest(self, sock, sessionDict):
        """
        Sends a handshake byte, obtains the content length from
        the value of the first ten bytes read, and then reads no
        more than that amount, which it marshals with the 'marshal'
        module. Finally, returns the marshalled request data
        """
        SocketScience.send_it_all(sock, '\0')
        DEBUG(AECGI, 'sent sentinel')
        lenDataStr = SocketScience.read_this_many(sock, 10)
        DEBUG(AECGI, 'read length')
        lenData = int(lenDataStr)
        data = SocketScience.read_this_many(sock, lenData)
        DEBUG(AECGI, 'read request data')
        marcia=marshal.loads(data)
        return marcia

    def marshalResponse(self, response, sessionDict):
        '''
        return response data, with the first ten bytes indicating
        the content length.
        '''
        return self._marshalData(response)

    def marshalException(self, exc_text, sessionDict):
        '''
        should return response data appropriate for the current exception.
        '''
        res=RequestFailed(Configuration.job,
                          exc_text,
                          sessionDict)
        if res:
            return self._marshalData(res)
        else:
            return self._marshalData(exc_text)

    def _marshalData(self, data):
        return "%10d%s" %(len(data), data)

def _serverStartHook(*args, **kw):
    requestHandler.requestHandler.addRequestHandler(AecgiProtocol(),
                                                    Configuration.AecgiListenPorts)    

Configuration.mergeDefaults(AecgiListenPorts=['TCP:localhost:9888'])
if Configuration.AecgiListenPorts:
    Hooks.ServerStart.append(_serverStartHook)

