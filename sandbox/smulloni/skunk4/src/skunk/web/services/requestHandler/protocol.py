
from skunk.util.hooks import Hook
RequestFailed=Hook()


# abstract class for protocols used in handling request and response

class Protocol(object):
    """
    abstract class for protocols used in handling request and response
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

    def marshalException(self, exc_text, ctxt):
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

        

