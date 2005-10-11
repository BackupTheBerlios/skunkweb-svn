from skunk.web.config import mergeDefaults
from skunk.util.hooks import Hook
from skunk.util.gziputil import TimelessGzipFile
from skunk.web.util.status import http_statuses, headersonlyStatuses

mergeDefaults(textCompression=False,
              generateEtagHeader=True,
              HttpLoggingOn=False)

headersOnlyMethods=('HEAD',)

# hooks declared here
HaveConnection=Hook()
PreHandleConnection=Hook()
HandleConnection=Hook()
ProcessResponse=Hook()

class Redirect(Exception):
    pass

class NullOutput:
    def write(self, *args): pass
    def getvalue(self):
        return ''

def _processRequest(requestData, ctxt):
    """
    request handling functioning for requestHandler's
    HandleRequest hook.
    """
    response=None
    connection=HTTPConnection(requestData)

    ctxt['CONNECTION']=connection
    ctxt['HOST']=connection.host
    ctxt['LOCATION']=connection.uri
    ctxt['SERVER_PORT']=int(connection.env['SERVER_PORT'])
    try:
        HaveConnection(connection, ctxt)

        # overlay of config information
        updateConfig(ctxt)
        PreHandleConnection(connection, ctxt)
                
    except PreemptiveResponse, pr:
        response=pr.responseData
    except:
        exception("error in handling web request:")
    else:
        response=HandleConnection(connection, ctxt)

    # so the response can be further processed, add it to the ctxt temporarily
    ctxt['RESPONSE']=response
    ProcessResponse(connection, ctxt)
    response=ctxt.pop('RESPONSE')
    
    # the connection should be available to postResponse and cleanup hooks.
    ctxt['CONNECTION']=connection
    return response


def _cleanupConfig(requestData, ctxt):
    """
    function for requestHandler's CleanupRequest hook
    """
    for k in ('HOST', 'LOCATION', 'SERVER_PORT'):
        if ctxt.has_key(k):
            del ctxt[k]
    updateConfig(ctxt)

def _compressit(txt):
    outt = cStringIO.StringIO()
    outf = TimelessGzipFile(fileobj=outt, mode='wb')
    outf.write(txt)
    outf.close()
    retval = outt.getvalue()
    return retval
    
def _accesslog(requestData, ctxt):
    if Configuration.HttpLoggingOn:
        conn=ctxt.get('CONNECTION')
        if conn:
            # very tolerant of env being screwed up
            HTTP_ACCESS(remote=conn.env.get('REMOTE_ADDR', '-'),
                        request="%s %s %s" % (conn.method,
                                              conn.uri,
                                              conn.env.get('SERVER_PROTOCOL', '-')),
                        status=conn._status,
                        length=len(conn._rawOutput),
                        auth_user=conn.env.get('REMOTE_USER', '-'))
    
