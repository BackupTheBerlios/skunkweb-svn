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
#!/usr/local/bin/python

import sys, os

def getcd():
    cwd = os.getcwd()

    if os.path.islink(sys.argv[0]):
        bn = os.path.basename(sys.argv[0])
        sc = os.readlink(bn)
    else:
        sc = sys.argv[0]

    os.chdir(os.path.dirname(sc) or '.')

    inst = os.getcwd()
    os.chdir(cwd)
    return inst