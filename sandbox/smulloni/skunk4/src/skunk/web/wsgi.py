import os

# server side -- code for marshalling the web data into wsgi form and
# invoking the wsgi application

def getEnvironBase(instream,
                   errstream,
                   env=None,
                   multithread=False,
                   multiprocess=True,
                   run_once=False):
    if env is None:
        env=os.environ
    # copy in a manner to ensure that environ is a dict
    environ=dict(env.items())
    environ['wsgi.input']=instream
    environ['wsgi.errors']=errstream
    environ['wsgi.version']=(1,0)
    environ['wsgi.multithread']=multithread
    environ['wsgi.multiprocess']=multiprocess
    environ['wsgi.run_once']=run_once

    if environ.get('HTTPS','off') in ('on','1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'
    
    return environ

class WSGIRunner(object):
    def __init__(self,
                 stdin,
                 stderr,
                 stdout,
                 serverName,
                 serverPort):
        self.stdin=stdin
        self.stderr=stderr
        self.stdout=stdout
        self.serverName=serverName
        self.serverPort=serverPort
        self._setup_environ()

    def _setup_environ(self):
        e=self._envbase={}
        e['SERVER_NAME']=self.serverName
        e['GATEWAY_INTERFACE']='CGI/1.1'
        e['SERVER_PORT']=str(self.serverPort)
        e['REMOTE_HOST']=''
        e['CONTENT_LENGTH']=''
        e['SCRIPT_NAME']=''
        
    def run(self, application):
        environ=getEnvironBase(self.stdin, self.stderr)
        
        headers_set = []
        headers_sent = []

        def write(data):
            assert headers_set, "write() before start_response()"
            
        elif not headers_sent:
            # Before the first output, send the stored headers
            status, response_headers = headers_sent[:] = headers_set


            # See if Content-Length is given.
            found = False
            for name, value in response_headers:
                if name.lower() == 'content-length':
                    found = True
                    break
                
                # If not given, try to deduce it if the iterator implements
                # __len__ and is of length 1. (data will be result[0] in this
                # case.)
                if not found and result is not None:
                    try:
                        if len(result) == 1:
                            response_headers.append(('Content-Length',
                                                     str(len(data))))
                    except:
                        pass

                    
            self.stdout.write('Status: %s\r\n' % status)
            for header in response_headers:
                self.stdout.write('%s: %s\r\n' % header)
                self.stdout.write('\r\n')
                
                self.stdout.write(data)
                self.stdout.flush()

        def start_response(status,response_headers,exc_info=None):
            if exc_info:
                try:
                    if headers_sent:
                        # Re-raise original exception if headers sent
                        raise exc_info[0], exc_info[1], exc_info[2]
                finally:
                    exc_info = None     # avoid dangling circular ref
            else:
                assert not headers_set, "Headers already set!"
            
            headers_set[:] = [status,response_headers]
            return write

        result = application(environ, start_response)
        try:
            for data in result:
                if data:    # don't send headers until body appears
                    write(data)
            if not headers_sent:
                write('')   # send headers now if body was empty
        finally:
            if hasattr(result,'close'):
                result.close()

# client (application) side -- api for wrapping the wsgi-formatted
# data into a thread-local global object.  (I'm turning my back on my
# attempt at purity in stoat and going with thread-locals big time!).
# This api should work outside of skunkweb itself, in, say, a wsgikit
# runner.

WSGIConnection(object):
    def __init__(env, stdin, stdout):
        self._env=env
        self._stdin=stdin
        self._stdout=stdout

    def requestCookie():
        def fget(self):
            if hasattr(self, '_requestCookie'):
                return self._requestCookie
            cookie=SimpleCookie()
            if self._env.has_key('HTTP_COOKIE'):
                try:
                    cookie.load(self._env['HTTP_COOKIE'])
                except CookieError:
                    exception("error loading cookie")
            self._requestCookie=cookie
            return cookie
        doc="the cookie submitted with the client request"
        return fget, None, None, doc
    requestCookie=property(*requestCookie())

    def requestPath():
        def fget(self):
            return self._env.get('SCRIPT_NAME', '')+self._env.get('PATH_INFO', '')
        return fget
    requestPath=property(requestPath())

    def method():
        def fget(self):
            return self._env['REQUEST_METHOD'].upper()
        return fget
    method=property(method())

    def querystring(
        

