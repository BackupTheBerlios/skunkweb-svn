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
import SocketMan
import sys
sys.stderr = sys.__stderr__
def handleconn(sock, addr):
    sock.send("foo! %s\n" % (sock.getsockname(),))
    raise "SHIT"
    
sm = SocketMan.SocketMan(numProcs=3, pidFile='pid')
#sm.addConnection(("UNIX", "foo", 0555), handleconn)
sm.addConnection(("TCP", "", 9991), handleconn)
sm.moduleSnapshot()
print "got here!", sm.mainloop
sm.mainloop()
