# $Id: importer.py,v 1.1 2002/02/16 06:37:00 smulloni Exp $
# Time-stamp: <02/02/16 01:31:56 smulloni>

######################################################################## 
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
########################################################################

# this should add an import hook so that python modules can be imported from
# the vfs.  It makes no attempt to load c modules or to check the timestamps of
# pyc files.

import os
import marshal
import imp
import imputil
import types

MAGIC_LEN=8 # len(imp.get_magic()) + 4 for a timestamp

def _importpyc(bytes, name):
    return marshal.loads(bytes[MAGIC_LEN:])
def _importpy(bytes, name):
    return compile(bytes, '%s.py' % name, 'exec')
suffixes=[('.pyc', _importpyc), ('.py', _importpy)]


class VFSImporter(imputil.Importer):

    def __init__(self, fs, path):
        self.fs=fs
        self.path=path

    def get_code(self, parent, modname, fqname):
        # print "in get_code: %s, %s, %s" % (parent, modname, fqname)
        if parent==None:
            pname=''
        elif type(parent)==types.ModuleType:
            pname=parent.__name__
        else:
            pname=parent
        
        for p in self.path:
            # try package
            dirname=os.path.join(p, modname)
            if self.fs.isdir(dirname):
                initmod='%s.%s' % (modname, '__init__')
                result=self.get_code(modname, '__init__', initmod)
                if result:
                    return 1, result[1], result[2]
                else:
                    return None
            # not a package
            for suffix, importFunc in suffixes:
                filename=os.path.join(p, "%s%s" % (os.path.join(pname, modname), suffix))
                # print "testing filename %s" % filename
                if self.fs.exists(filename):
                    # bingo
                    # print "found!"
                    bytes=self.fs.open(filename).read()
                    return 0, importFunc(bytes, modname), {}


def test():
    import vfs
    fs=vfs.LocalFS('/home/smulloni/')
    myimp=VFSImporter(fs, ['/python'])
    import sys
    imputil.ImportManager().install()
    sys.path.append(myimp)
    import foofoo
    print foofoo

                    
                    
    
                    
