# $Id: __init__.py,v 1.1.2.2 2001/10/16 03:27:15 smulloni Exp $
# Time-stamp: <01/10/07 14:05:59 smulloni>

########################################################################  
#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
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

# a webdav server.

def __initFlag():
    import SkunkWeb.ServiceRegistry as sr
    sr.registerService('webdav')

def __initConfig():
    import SkunkWeb.Configuration as C
    import os
    C.mergeDefaults(
        webdavDB=os.join(C.SkunkRoot, 'var/run/WEBDAVdb'),
        webdavFS=fs.WebdavFS(),
        )
    
    

def __initHooks():
    import web.protocol as wp
    import SkunkWeb.constants
    import handlers
    SkunkWeb.constants.DAV_JOB='/webdav/'
    jobGlob="%s%s*" % (SkunkWeb.constants.WEB_JOB,
                       SkunkWeb.constants.DAV_JOB)
    wp.HandleConnection[jobGlob]=handlers.handleConnection
