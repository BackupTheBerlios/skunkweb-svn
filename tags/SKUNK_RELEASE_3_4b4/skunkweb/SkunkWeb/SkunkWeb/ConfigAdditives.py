# $Id: ConfigAdditives.py,v 1.8 2003/05/01 20:45:55 drew_csillag Exp $
# Time-stamp: <03/04/22 18:07:34 smulloni>
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>,
#                     Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   

########################################################################

__all__=['Location',
         'File',
         'Host',
         'Port',
         'ServerPort',
         'IP',
         'UNIXPath',
         'Scope',
         'Include']

from SkunkWeb.Hooks import ServerStart
import scope
import ConfigLoader
import KickStart

def _createMatcher(matcherClass, paramName, paramVal, kids, kw):
    m=matcherClass(paramName, paramVal, kw)
    if kids:
        m.addChildren(*kids)
    return m

def Location(path, **kw):
    return _createMatcher(scope.SimpleStringMatcher,
                          'location',
                          path,
                          None,
                          kw)

def File(path, **kw):
    return _createMatcher(scope.RegexMatcher,
                          'location',
                          path,
                          None,
                          kw)

def Host(hostname, *kids, **kw):
    return _createMatcher(scope.GlobMatcher,
                          'host',
                          hostname,
                          kids,
                          kw)

def Port(port, *kids, **kw):
    return _createMatcher(scope.StrictMatcher,
                          'port',
                          port,
                          kids,
                          kw)

def ServerPort(port, *kids, **kw):
    return _createMatcher(scope.StrictMatcher,
                          'server_port',
                          port,
                          kids,
                          kw)

def IP(ip, *kids, **kw):
    return _createMatcher(scope.StrictMatcher,
                          'ip',
                          ip,
                          kids,
                          kw)

def UNIXPath(path, *kids, **kw):
    return _createMatcher(scope.GlobMatcher,
                          'unixpath',
                          path,
                          kids,
                          kw)                       

def Scope(*scopeMatchers):
    from SkunkWeb import Configuration
    Configuration.addScopeMatchers(*scopeMatchers)

def Include(filename):
    ConfigLoader.loadConfigFile(filename, KickStart.CONFIG_MODULE)
        
def importConfiguration():
    # have to do this here since this is imported before the configuration
    # "module" has been put in place
    global Configuration
    from SkunkWeb import Configuration    


ServerStart.append(importConfiguration)


########################################################################
# $Log: ConfigAdditives.py,v $
# Revision 1.8  2003/05/01 20:45:55  drew_csillag
# Changed license text
#
# Revision 1.7  2003/04/23 02:14:31  smulloni
# removing import of scopeable
#
# Revision 1.6  2002/09/30 20:02:27  smulloni
# support for scoping based on SERVER_PORT.
#
# Revision 1.5  2002/07/15 15:07:10  smulloni
# various changes: configuration (DOCROOT); new sw.conf directive (File);
# less spurious debug messages from rewrite; more forgiving interface to
# MsgCatalog.
#
# Revision 1.4  2002/03/30 20:05:27  smulloni
# added Include directive for sw.conf; fixed IP bug (was being clobbered in sw.conf)
#
# Revision 1.3  2001/10/02 02:35:34  smulloni
# support for scoping on unix socket path; very serious scope bug fixed.
#
# Revision 1.2  2001/09/09 02:37:41  smulloni
# performance enhancements, removal of sundry nastinesses and erasure of
# reeking rot.
#
# Revision 1.1.1.1  2001/08/05 14:59:37  drew_csillag
# take 2 of import
#
#
# Revision 1.11  2001/07/09 20:38:40  drew
# added licence comments
#
# Revision 1.10  2001/05/04 18:38:52  smullyan
# architectural overhaul, possibly a reductio ad absurdum of the current
# config overlay technique.
#
# Revision 1.9  2001/05/03 17:26:12  smullyan
# added an IP pseudo-directive to SkunkWeb.ConfigAdditives; Host now matches
# strictly (perhaps it should be a glob); port and ip are now put in
# sessionDict by requestHandler; HTTPConnection's "host" field is now the host
# header, if any, with the port removed.
#
# Revision 1.8  2001/05/03 16:14:59  smullyan
# modifications for scoping.
#
# Revision 1.7  2001/05/01 23:03:39  smullyan
# added support for name-based virtual hosts.
#
########################################################################
