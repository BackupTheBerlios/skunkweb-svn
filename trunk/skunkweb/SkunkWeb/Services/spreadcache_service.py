# Time-stamp: <03/04/15 00:23:55 smulloni>
# $Id: spreadcache_service.py,v 1.2 2003/05/01 20:45:53 drew_csillag Exp $

########################################################################  
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#
########################################################################

from SkunkWeb import Configuration
import spreadcache

Configuration.mergeDefaults(SpreadConnectParams={})

for alias, params in Configuration.SpreadConnectParams.items():
    spreadcache.initAlias(alias, **params)
