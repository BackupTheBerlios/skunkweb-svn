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
# $Id: UrlBuilder.py,v 1.6 2003/02/08 03:23:44 smulloni Exp $
# Time-stamp: <01/04/25 16:10:18 smulloni>
########################################################################
"""
This is the module responsible for building URLs for basic templating 
personality

Services desiring more complex naming schemes should write their own
functions and / or tags which would utilize them.
"""



import types
import urllib

import DT
import skunklib
from SkunkExcept import *
import AE.Component
from web.protocol import Redirect
from SkunkWeb.LogObj import DEBUG
from SkunkWeb.ServiceRegistry import TEMPLATING
import SkunkWeb.Configuration as Config

# for img tag, try to import PIL (to get default image width and height)
try:
    import PIL.Image as Image
    import AE.Cache as Cache
    _havePIL=1
    import pil_preload
except:
    _havePIL=0

Config.mergeDefaults(tagsGenerateXHTML=1)
                     

def _genUrl ( path, query = {}, need_full = 0, noescape=None ):
    """
    Generate the URL given a URI. If need_full is 1, the generated URL 
    will contain the server part.
    """

    if noescape is None:
	path = urllib.quote(path)

    if query:
        path = path + skunklib.urlencode ( query )

    if need_full:
        if path[0] != '/':
            raise SkunkRuntimeError, \
                'full url being generated with relative path: %s' % path
        conn=AE.Component.componentStack[0].namespace['CONNECTION']
        if conn.env.get('HTTPS')=='on':
            scheme='https'
        else:
            scheme='http'
        host=conn.requestHeaders.get('Host')
        if not host:
            host=conn.env.get('SERVER_NAME')
            port=conn.env.get("SERVER_PORT")
            if port:
                if (scheme=='http' and not port=='80') or (scheme=='https' and not port=='443'):
                    host='%s:%s' % (host, port)
        url='%s://%s%s' % (scheme, host, path)

    else:
        url = path

    return url

def _genKwArgs ( kwargs ):
    """
    Add keyword arguments to tags
    """
    ret = ''
    for k, v in kwargs.items():
        ret = ret + ' %s="%s"' % (k, v)

    return ret

def url (path, queryargs, text = None,
         kwargs = {}, noescape = None, need_full=None,
         url = None):
    """
    The url function we expose.

    Returns either the url part of the request (http://path) or (if text is not
    None) the complete link:
    <A href="http://path">text</A>

    If 'url' is given, it is used in place of path / query
    """
    if not url:
         url = _genUrl(path, query = queryargs, noescape=noescape, need_full=need_full)

    # Generate the URL 
    if text is not None:
        # Use the kwargs here
        ret = '<a href="%s"%s>%s</a>' % ( url, _genKwArgs(kwargs), text )
    else:
        ret = url

    return ret

def image ( path, queryargs = None, kwargs={}, noescape = None  ):
    """
    Create an image tag
    """
    if _havePIL and not path.startswith('http://'):
        lckws=[x.lower() for x in kwargs]
        if not filter(lambda x: x in ('height', 'width'), lckws):
            try:
                im=Image.open(Cache._openDocRoot(path))
                kwargs['width'], kwargs['height']=im.size
            except:
                DEBUG(TEMPLATING, "failed to read doc root for path %s" % path)
    if Config.tagsGenerateXHTML:
        template='<img src="%s"%s />'
    else:
        template='<img src="%s"%s>'
    ret = template % (_genUrl(path,
                              query=queryargs, 
                              noescape=noescape),
                      _genKwArgs(kwargs))

    return ret

def form ( path, kwargs = {}, noescape = None ):
    """
    Create a form tag
    """

    return '<form action="%s"%s>' % (_genUrl(path, noescape=noescape), _genKwArgs ( kwargs ))

def redirect ( path = None, url = None, queryargs = {}, 
               noescape = None, ):
    """
    Issue a redirect
    """

    if not url and not path:
        raise SkunkStandardError, 'either url or path argument must be given'
    elif url and path:
        raise SkunkStandardError, 'only one of url or path arguments needed'

    if not url:
        # This is a path, and needs http://hostname prepended
	# the tag code guarantees that the REQUEST object is available
	# to the tag (i.e. a cached component is not trying to suck
	# the server name out of REQUEST!)
        url = _genUrl ( path, query = queryargs, 
                        need_full = 1, noescape=noescape )

    # The url should already be a fully qualified URL by now
    AE.Component.componentStack[0].namespace['CONNECTION'].redirect(url)
    raise Redirect()

def hidden ( dict ):
    """
    Make hidden form fields for the items in the dictionry
    """
    if Config.tagsGenerateXHTML:
        template='<input type="hidden" name="%s" value="%s" />'
    else:
        template='<input type="hidden" name="%s" value="%s">' 
    l = []
    for k,v in dict.items():
        enck = DT.DTUtil.htmlquote(str(k))
        if type(v) == types.ListType:
            for vi in v:
                if vi is None:
                    encv = ""
                else:
                    encv=DT.DTUtil.htmlquote(str(vi))
                l.append(template % (enck, encv))
        else: 
            if v is None:
                encv = ""
            else:
                encv=DT.DTUtil.htmlquote(str(v))
            l.append(template % (enck, encv))
    return '\n'.join(l)

