########################################################################
# $Id: protocol.py,v 1.19 2003/03/20 21:04:11 smulloni Exp $
# Time-stamp: <03/03/20 16:01:11 smulloni>
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
#   
########################################################################

from SkunkExcept import SkunkCriticalError
from SkunkWeb.LogObj import DEBUG, logException
from SkunkWeb.ServiceRegistry import WEB
from SkunkWeb import Configuration, ConfigAdditives, constants
from requestHandler.protocol import Protocol, PreemptiveResponse
import Cookie
import Date
import SocketScience
import cStringIO
import cgi
import marshal
import sys
import time
import types
import browser
from SkunkWeb.Hooks import KeyedHook
import argextract

headersOnlyMethods=['HEAD'] 
headersOnlyStatuses=[100, 101, 102, 204, 304]

HaveConnection=KeyedHook()
PreHandleConnection=KeyedHook()
HandleConnection=KeyedHook()


class HTTPConnection:
    '''
    The connection object used for HTTP, passed to various web hooks.
    '''
    def __init__(self, requestData):
        self._output=cStringIO.StringIO()
        self.env = requestData['environ']
        self._requestDict=requestData
        self._status=200
        self._stdin = requestData['stdin']
        self._initURI(self.env)
        self._initArgs(requestData)
        self._initHeaders()
        self._initCookies()
        
        self.browser = browser.Browser(self.requestHeaders.get('User-Agent'))
        # for convenience -- possibly expand this, possibly eliminate it
        self.method=self.env['REQUEST_METHOD']
        
        # possibly this field, although harmless, should not be here,
        # the extraction of the port-less host should be done
        # in _processRequest -- CONSIDER ***
        fullHost=self.requestHeaders.get("Host", "")
        # get rid of port, it confuses matching by host
        colindex=fullHost.find(':')
        if colindex!=-1:
            fullHost=fullHost[:colindex]
        self.host=fullHost

    def write(self, s):
        self._output.write(s)
        
    def _initArgs(self, requestData):
        stdin = cStringIO.StringIO(requestData['stdin'])
        env = requestData['environ']
        try:
            query = cgi.FieldStorage(fp = stdin, environ = env,
                                     keep_blank_values = 1)
            self.args=self._convertArgs(query)
            ok=1
        except:
            # may be some exotic content-type
            logException()
            DEBUG(WEB, "content-type: %s" % self.requestHeaders.get("content-type"))
            self.args={}
            ok=0

        if ok and Configuration.mergeQueryStringWithPostData and \
               env.get("REQUEST_METHOD")=='POST':
            #if POST, see if any GET args too
            environ = env.copy()
            environ["REQUEST_METHOD"] = 'GET'            
            query = cgi.FieldStorage(fp = stdin, environ = environ,
                                     keep_blank_values = 1)
            self.args.update(self._convertArgs(query))
        
    def _convertArgs(self, query):
        d = {}
        if query!=None:
            try:
                keys=query.keys()
            except TypeError:
                # annoyingly thrown by cgi.py in some circumstances
                DEBUG(WEB, "TypeError thrown in _convertArgs for query %s" % query)
                return d
            for k in keys:
                d[k] = self._convertArg(query[k])
        return d

    def _convertArg(self, val):
        if type(val) in (types.ListType, types.TupleType):
            return map(self._convertArg, val)
        if val.filename:
            return _File(val)
        return val.value

    def extract_args(self, *args, **kwargs):
        
        """
        extracts and returns a dictionary of the specified fields
        from self.args.  args are argument names to look for; they
        will be placed in the dictionary unconverted, or None if not
        found.  The values for kwargs may be one of three forms:
        
          1. a default value (which must not be a sequence and not callable);
          2. a callable object, which will be taken to be a conversion function;
          3. a sequence of length one or two, the first item of which must
             be a callable and will be used as a conversion function, and the
             second item of which, if present, will be used as a default value.

        This is supposed to be equivalent to the <:args:> tag in STML.
        """
        return argextract.extract_args(self.args, *args, **kwargs)

    def _initHeaders(self):
        self.requestHeaders = HeaderDict(self._requestDict['headers'])
        self.responseHeaders = HeaderDict({
            #'Server': 'SkunkWeb %s' % Configuration.SkunkWebVersion,
            'Date': str(Date.HTTPDate(time.time())),
            'Status': '200 OK'
            })

    def _initCookies(self):
        self.requestCookie = Cookie.SimpleCookie()
        if self.requestHeaders.has_key('Cookie'):
            try:
                self.requestCookie.load(self.requestHeaders['Cookie'])
            except Cookie.CookieError:
                logException()
        self.responseCookie = Cookie.SimpleCookie()        

    def _initURI(self, env):
        self.uri=self.realUri = env.get('SCRIPT_NAME', '') + env.get('PATH_INFO', '')

    def setContentType(self, type):
        self.responseHeaders['Content-Type'] = type
        
    def response(self):
        rawOutput, headers = self._output.getvalue(), ''
        if not self.responseHeaders.has_key('Content-Length'):
            self.responseHeaders['Content-Length'] = len(rawOutput)
        if self.responseCookie.keys():
            headers = headers + str(self.responseCookie) + '\r\n'
        for i in self.responseHeaders.items():
            headers = headers + "%s: %s\r\n" % i
        if self.method in headersOnlyMethods or self._status in headersOnlyStatuses:
            return headers+"\r\n"
        else:
            return headers + "\r\n" + rawOutput
    
    def setStatus(self, status):
        try:
            self.responseHeaders['Status'] = _http_statuses[status]
        except KeyError:
            raise SkunkCriticalError, 'invalid status: %s' % status
        self._status = status
        
    def redirect(self, url):
        self.responseHeaders['Location'] = url
        self.setStatus(301)
        self._output=NullOutput()
        DEBUG(WEB, "Redirecting to %s" % url)
        
########################################################################

class _File:
    def __init__(self, val):
        self.contents, self.filename = val.value, val.filename

    def __str__(self):
        return 'Uploaded file %s -- use obj.contents to get contents' % self.filename

########################################################################
    
class Redirect(Exception):
    pass

########################################################################

class NullOutput:
    def write(self, *args): pass
    def getvalue(self):
        return ''

########################################################################
import skunklib
class HeaderDict:
    '''
    dictionary class that stores headers and formats them consistently.
    '''
    def __init__(self, initval={}):
        self._fixHeader = skunklib.normheader
        self._d = {}
        for k, v in initval.items():
            self._d[self._fixHeader(k)] = v

    def __getitem__(self, d):
        return self._d[self._fixHeader(d)]

    def __setitem__(self, k, v):
        self._d[self._fixHeader(k)] = v

    def __repr__(self):
        return repr(self._d)

    def has_key(self, k):
        return self._d.has_key(k)

    def get(self, k, default=None):
        return self._d.get(k, default)

    def items(self):
        return self._d.items()

    def _fixHeader(self, s):
        '''
        utility function for formatting headers in a consistent manner.
        '''
        return '-'.join([i.capitalize() for i in s.split('-')])

########################################################################

#
# The verbose status table
#
_http_statuses = { 
 100: '100 Continue',
 101: '101 Switching Protocols',
 102: '102 Processing',
 200: '200 OK',
 201: '201 Created',
 202: '202 Accepted',
 203: '203 Non-Authoritative Information',
 204: '204 No Content',
 205: '205 Reset Content',
 206: '206 Partial Content',
 207: '207 Multi-Status',
 300: '300 Multiple Choices',
 301: '301 Moved Permanently',
 302: '302 Found',
 303: '303 See Other',
 304: '304 Not Modified',
 305: '305 Use Proxy',
 306: '306 unused',
 307: '307 Temporary Redirect',
 400: '400 Bad Request',
 401: '401 Authorization Required',
 402: '402 Payment Required',
 403: '403 Forbidden',
 404: '404 Not Found',
 405: '405 Method Not Allowed',
 406: '406 Not Acceptable',
 407: '407 Proxy Authentication Required',
 408: '408 Request Time-out',
 409: '409 Conflict',
 410: '410 Gone',
 411: '411 Length Required',
 412: '412 Precondition Failed',
 413: '413 Request Entity Too Large',
 414: '414 Request-URI Too Large',
 415: '415 Unsupported Media Type',
 416: '416 Requested Range Not Satisfiable',
 417: '417 Expectation Failed',
 418: '418 unused',
 419: '419 unused',
 420: '420 unused',
 421: '421 unused',
 422: '422 Unprocessable Entity',
 423: '423 Locked',
 424: '424 Failed Dependency',
 500: '500 Internal Server Error',
 501: '501 Method Not Implemented',
 502: '502 Bad Gateway',
 503: '503 Service Temporarily Unavailable',
 504: '504 Gateway Time-out',
 505: '505 HTTP Version Not Supported',
 506: '506 Variant Also Negotiates',
 507: '507 Insufficient Storage',
 508: '508 unused',
 509: '509 unused',
 510: '510 Not Extended'}

########################################################################

def _processRequest(requestData, sessionDict):
    """
    request handling functioning for requestHandler's
    HandleRequest hook.
    """
    response=None
    
    DEBUG(WEB, 'creating Connection')
    DEBUG(WEB, 'requestData is %s' % str(requestData))
    connection=HTTPConnection(requestData)

    sessionDict[constants.CONNECTION]=connection
    sessionDict[constants.HOST]=connection.host
    sessionDict[constants.LOCATION]=connection.uri
    sessionDict[constants.SERVER_PORT]=int(connection.env['SERVER_PORT'])
    try:
        DEBUG(WEB, 'executing HaveConnection hook')
        HaveConnection(Configuration.job, connection, sessionDict)
        DEBUG(WEB, 'survived HaveConnection hook')

        # overlay of config information
        Configuration.trim()
        Configuration.scope(sessionDict)
        #Configuration.saveMash()

        DEBUG(WEB, 'executing PreHandleConnection hook')
        PreHandleConnection(Configuration.job, connection, sessionDict)
                
    except PreemptiveResponse, pr:
        DEBUG(WEB, 'got preemptive response')
        response=pr.responseData
    except:
        logException()
    else:
        DEBUG(WEB, 'handling connection')
        HandleConnection(Configuration.job, connection, sessionDict)
        response=connection.response()

    # the connection should be available to postResponse and cleanup hooks.
    sessionDict[constants.CONNECTION]=connection
    DEBUG(WEB, 'returning response: %s' % response)
    if response!=None:
        DEBUG(WEB, 'length of response: %d' % len(response))
    return response


def _cleanupConfig(requestData, sessionDict):
    """
    function for requestHandler's CleanupRequest hook
    """
    if sessionDict.has_key(constants.HOST):
        del sessionDict[constants.HOST]
    if sessionDict.has_key(constants.LOCATION):
        del sessionDict[constants.LOCATION]
    if sessionDict.has_key(constants.SERVER_PORT):
        del sessionDict[constants.SERVER_PORT]
    Configuration.trim()

    if sessionDict.has_key(constants.IP):
        Configuration.scope({constants.IP : sessionDict[constants.IP],
                             constants.PORT: sessionDict[constants.PORT]})
    elif sessionDict.has_key(constants.UNIXPATH):
        Configuration.scope({constants.UNIXPATH : sessionDict[constants.UNIXPATH]})
    #Configuration.saveMash()

