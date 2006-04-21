"""

Contains a BaseController class suitable as a base class for
controllers, with some convenience methods.

"""

import SkunkWeb
from computils import stringcomp
import os
import re
import string
import time

_schemepat=re.compile('^[a-z]+://.*')

try:
    # python 2.5
    from httplib import responses as http_responses
except ImportError:
    import web.protocol as P
    http_responses=dict((x,y[4:]) for x, y in P._http_statuses.iteritems() if not y.endswith('unused'))
    del P


ERROR_TEMPLATES={
    'text/plain' : string.Template("$message"),
    'text/html' :  string.Template("<html><head><title>$message</title></head><body><h1>$message</h1></body></html>")}


class BaseController(object):

    def connection():
        def fget(self):
            return SkunkWeb.Context.connection
        return fget
    connection=property(connection())

    def http_error(self, status, message=None, mimetype=None, template=None):
        if status not in http_responses:
            raise ValueError, "invalid status: %s" % status
        if mimetype is None:
            mimetype=SkunkWeb.Configuration.defaultErrorMimetype
        elif mimetype not in ERROR_TEMPLATES:
            raise ValueError, "unsupported mimetype for error response: %s" % mimetype
        if message is None:
            message=http_responses[error]
        conn=self.connection
        conn.setStatus(status)
        if template is None:
            template=ERROR_TEMPLATES[status]
        else:
            if not hasattr(template, "safe_substitute"):
                template=string.Template(template)
        conn.setContentType(mimetype)
        return template.safe_substitute(message)
    

    def do404(self, message=None):
        # special case 404s to use the preexisting SkunkWeb 404 mechanism
        conn=self.connection
        conn.setStatus(404)
        conn.setContentType('text/html')
        return stringcomp(SkunkWeb.Configuration.notFoundTemplate,
                         message=message)

    def do401(self, message=None, mimetype=None, template=None):
        return self.http_error(status, message, mimetype, template)


    def redirect(self, url, status=301):
        if not _schemepat.match(url):
            url=os.path.normpath(os.path.join(self.connection.uri, url))
        self.connection.redirect(url, status)
        return "redirecting to %s" % url

    def flash(self, message):
        """
        flash a message into a cookie
        """
        cookie=self.connection.responseCookie
        cookie['flash']=message
        cookie['flash']['path']='/'
        cookie['flash']['expires']=time.time()+1000

    def get_flash(self, default=None):
        """
        get a flashed message
        """
        try:
            message=self.connection.requestCookie['flash'].value
        except KeyError:
            return default
        else:
            self.connection.responseCookie['flash']=''
            self.connection.responseCookie['flash']['expires']=-99999
            return message

        
    
__all__=['BaseController']
