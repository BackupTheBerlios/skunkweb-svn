# $Id: handlers.py,v 1.1.2.1 2001/09/27 03:36:07 smulloni Exp $
# Time-stamp: <01/09/24 21:32:21 smulloni>

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

import xmlutils
import sys
from SkunkWeb import Configuration

# cop-out; maybe this will come from somewhere else
davfs=Configuration.webdavFS

def handleConnection(conn, sessionDict):
    meth=conn.method
    handler='handle_%s' % meth.lower()
    if hasattr(sys.modules[__name__], handler):
        return handler(_uriToPath(conn.uri), conn, sessionDict)
    conn.setStatus(501) # or should it be 405?
    return 1

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
        conn.response=davfs.open(path).read()
        return 1
    else:
        conn.status=404 # or 405?
                    

def handle_put(path, conn, sessionDict):
    # this requires testing for locks, processing of if headers.
    pass

def handle_propfind(path, conn, sessionDict):
    # this requires parsing the xml body, checking for depth headers;
    # issuing request to _propfind().  status is 207, unless it is 404.
    pass

def _propfind(path, depth, type, props=None):
    pass

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
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################
