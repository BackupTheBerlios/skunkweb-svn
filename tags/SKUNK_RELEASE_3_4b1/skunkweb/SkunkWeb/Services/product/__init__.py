# $Id: __init__.py,v 1.4 2002/02/21 23:35:09 smulloni Exp $
# Time-stamp: <02/02/21 18:26:40 smulloni>

########################################################################
#  
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
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

"""
a service to support SkunkWeb products, which can be installed as
archive files (zip, tar, or tgz), or as directories in the SkunkWeb
product directory.  This service requires that the documentRootFS be a
MultiFS (at least prior to scoping); the assumption is that MultiFS
will become the default fs.

The product loader is configured to load by default all product
archives in the product directory, but can be configured to load any
arbitrary subset.

The loader opens the MANIFEST file in each archive, looks for
dependencies stated therein, and loads any products therein listed,
raising an error for circular or missing dependencies.  For each load,
it adds mount points to the MultiFS for the docroot and, by means of
an import hook in the vfs which permits python modules to be imported
from the vfs, adds the libs (if any) to sys.path.  Services specified
in the MANIFEST are then imported.

The MANIFEST is essentially an init file for the product which
integrates it into the SkunkWeb framework.  It must contain the
product version, and can also contain product dependencies and
services (python modules that use SkunkWeb hooks, to be imported at
product load time).  See manifest.py for details.

By default, a product's docroot will be mounted at
products/<product-name>, relative to the SkunkWeb documentRoot.  This
can be altered by modifying Configuration.defaultProductPath, which
will affect all products, or by adding the product-name to the
Configuration.productPaths mapping.

This service will also contain a utility for creating products, creating
the MANIFEST file, byte-compiling the python modules, and creating the
archive file.
"""

import SkunkWeb.Configuration as Cfg
from loader import *
from manifest import *
import os

Cfg.mergeDefaults(productDirectory='products',
                  products='*',
                  defaultProductPath='products',
                  productPaths={},
                  )

proddir=loader.product_directory()
if not os.path.isdir(proddir):
    try:
        os.makedirs(proddir)
    except:
        ERROR(("product service needs a product directory,"
               "currently configured as %s") % proddir)
        raise
del proddir

for p in loader.listProducts():
    p.load()


