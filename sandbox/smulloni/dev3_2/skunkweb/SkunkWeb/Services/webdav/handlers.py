b# $Id$
# Time-stamp: <01/10/14 13:24:51 smulloni>

######################################################################## 
#  Copyright (C) 2001 Jocob Smullyan <smulloni@smullyan.org>
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
########################################################################

import os
import sys
import xmlutils
from SkunkWeb import Configuration
from SkunkWeb.LogObj import DEBUG
from SkunkWeb.ServiceRegistry import WEBDAV
import fs
from constants import *

XMLElement=xmlutils.XMLElement

class StatusException(Exception):
    pass

class Response:
    def __init__(self, href, propstatList, responseDescription=None):
        self.href=href
        self.propstatList=propstatList
        self.responseDescription=responseDescription

    def toXML(self):
        responseElem=XMLElement(RESPONSE_ELEM, namespace=DAV_NS)
        hrefElem=XMLElement(HREF_ELEM)
        hrefElem.addChild(self.href)
        responseElem.addChild(hrefElem)
        for elem in self.propstatList:
            responseElem.addChild(elem.toXML())
        if self.responseDescription!=None:
            descElem=XMLElement(RESPONSEDESCRIPTION_ELEM)
            descElem.addChild(self.responseDescription)
            responseElem.addChild(descElem)
        return responseElem
        
class Propstat:
    def __init__(self, prop, status, responseDescription=None):
        self.prop=prop
        self.status=status
        self.responseDescription=responseDescription

    def toXML(self):
        propstatElem=XMLElement(PROPSTAT_ELEM, namespace=DAV_NS)
        propstatElem.addChild(prop)
        propstatElem.addChild(status)
        if self.responseDescription!=None:
            descElem=XMLElement(RESPONSEDESCRIPTION_ELEM)
            descElem.addChild(self.responseDescription)
            propstatElem.addChild(descElem)          
        return propstatElem

class Multistatus:
    def __init__(self, responseList, responseDescription=None):
        self.responseList=responseList
        self.responseDescription=responseDescription

    def toXML(self):
        multiElem=XMLElement(MULTISTATUS_ELEM, namespace=DAV_NS)
        multiElem.addChild(*[e.toXML() for e in self.responseList])
        if self.responseDescription!=None:
            multiElem.addChild(XMLElement(RESPONSEDESCRIPTION_ELEM).addChild( \
                self.responseDescription))
        return multiElem

# This needs to implement PathPropertyStore as well as FS;
# the default is fs.WebdavFS
davfs=Configuration.webdavFS

def handleConnection(conn, sessionDict):
    """
    delegates to http method-specific handler methods
    """
    meth=conn.method
    handler='handle_%s' % meth.lower()
    if hasattr(sys.modules[__name__], handler):
        try:
            return handler(_uriToPath(conn.uri), conn, sessionDict)
        except StatusException, s:
            conn.setStatus(s.args[0])
            return 1
    conn.setStatus(501) # or should it be 405?
    return 1

def _uriToPath(uri):
    if uri.startswith('/'):
        uri=uri[1:]
    return os.join(Configuration.documentRoot, uri)

# for each of the dav methods (not every method will need all of this):
# get xml body
# determine method parameters
# feed the latter to a method-specific routine
# in latter routine, do vfs/db work, marshal response to xml
# return xml data to methodhandler, which makes appropriate response

def handle_get(path, conn, sessionDict):
    # we don't do any dynamic processing here; just find the document
    # in the fs and return
    if davfs.exists(path) and davfs.isfile(path):
        conn.write(davfs.open(path).read())
        conn.setContentType(davfs.getproperty(path, GETCONTENTTYPE_PROP))
        return 1
    else:
        conn.setStatus(404) # or 405?                   

def handle_put(path, conn, sessionDict):
    # this requires testing for locks, processing of if headers.
    pass

def handle_propfind(path, conn, sessionDict):
    # this requires parsing the xml body, checking for depth headers;
    # status is 207, unless it is 404.
    depth=conn.requestHeaders.get(DEPTH_HEADER, 'infinity')
    DEBUG(WEBDAV, "unparsed xml document: %s" % conn.stdin)
    xmlelem=xmlutils.parse(conn._stdin)
    if not (xmlelem.name==PROPFIND_ELEM 
            and xmlelem.getNamespace()=DAV_NS):
        raise StatusException, 400    
    DEBUG(WEBDAV, "parsed xml document: %s" % str(xmlelem))
    # determine if resource exists
    if davfs.exists(path):
        responseBody, status=_propfindMultistatus(path,
                                                  depth,
                                                  _propfindType(xmlelem))
        conn.write(responseBody)
        conn.setContentType(XML_CONTENT_TYPE)
        conn.setStatus(status)
        return 1
    raise StatusException, 404
    return 1

def _propfindMultistatus(path, depth, typeElem):
    propstatdict={path: (404, {})}
    _propfindwalker(path, depth, typeElem, propstatdict)
    multistatus=XMLElement(MULTISTATUS_ELEM, 'D', DAV_NS)
    for p, data in propstatdict.items():
        response=XMLElement(RESPONSE_ELEM, 'D')
        href=XMLElement(HREF_ELEM, 'D')
        href.addChild(p)
        propstat=XMLElement(PROPSTAT_ELEM, 'D')
        prop=XMLElement(PROP_ELEM, 'D')
        status=XMLElement(STATUS_ELEM, 'D')
        status.addChild(data[0])
        for k, v in data[1]:
            newprop=XMLElement(k[1], namespace=k[0])
            if v != None:
                newprop.addChild(v)
            prop.addChild(newprop)
        propstat.addChild(prop)
        propstat.addChild(status)

def _propfindwalker(path, depth, typeElem, propstatdict):
    typename=typeElem.name
    is404=davfs.exists(path) 
    status=is404 and 'HTTP/1.1 200 OK' \
            or 'HTTP/1.1 404 Not Found'
    if not is404:
        if typename==ALLPROP_ELEM:        
            propstatdict[path]=(status, davfs.properties(path))
        elif typename=PROPNAME_ELEM:
            d={}
            for k in davfs.properties(path).keys():
                d[k]=None
            propstatdict[path]=(status, d)
        elif typename==PROP_ELEM:
            for elem in typeElem.getChildren():
                try:
                    propresult=davfs.getproperty(elem)
                except:
                    propresult=None
            status=
            propstatdict[path][(elem.getNamespace(), elem.name)]=(status, davfs.getproperty(elem))
    if depth=='1':
        depth='0'
    if davfs.isdir(path) and depth in ('1', 'infinity'):
        for res in davfs.listdir(path):
            _propfindwalker(res, depth, typeElem, propstatdict)


def _propfindType(propfindElem):
    # I expect exactly one DAV_NS element and
    # raise a Bad Request otherwise, but accept unknown elements.
    propfindChildren=filter(lambda x: isinstance(x, XMLElement) \
                            and x.getNamespace()==DAV_NS,
                            propfindElem.getChildren())
    if len(propfindChildren)==1:
        typeElem=propfindChildren[0]
        if typeElem.name in (ALLPROP_ELEM, PROP_ELEM, PROPNAME_ELEM):
            return typeElem
    raise StatusException, 400

def handle_proppatch(path, conn, sessionDict):
    pass

def handle_delete(path, conn, sessionDict):
    # check locks, If-headers
    if davfs.exists(path):
        davfs.remove(path)


def handle_mkdir(path, conn, sessionDict):
    pass

def handle_copy(path, conn, sessionDict):
    pass

def handle_move(path, conn, sessionDict):
    pass

def handle_options(path, conn, sessionDict):
    pass

def handle_post(path, conn, sessionDict):
    pass

def handle_lock(path, conn, sessionDict):
    pass

def handle_unlock(path, conn, sessionDict):
    pass
    
########################################################################
# $Log: handlers.py,v $
# Revision 1.1.2.2  2001/10/16 03:27:15  smulloni
# merged HEAD (basically 3.1.1) into dev3_2
#
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################
