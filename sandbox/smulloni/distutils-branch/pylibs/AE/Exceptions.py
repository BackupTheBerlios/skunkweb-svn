#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
#$Id$
import SkunkExcept

ReturnValue = "ReturnValue"

class TimeoutError ( SkunkExcept.SkunkCriticalError ):
    def __init__ ( self ):
        SkunkExcept.SkunkCriticalError.__init__ (
            self, 'a timeout has occured' )

