#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
Tag cache - description???
"""
# $Id: CacheTag.py,v 1.2 2003/05/01 20:45:58 drew_csillag Exp $

from CommonStuff import *
from DT import DTExcept

# The required modules
from Date import TimeUtil
import time

class CacheTag( DTTag ):
    """the <:cache:> tag"""
    def __init__(self):
        DTTag.__init__ ( self, 'cache', isempty=1,
                         modules = [ TimeUtil, time ] )

    def genCode(self, indent, codeout, tagreg, tag):
        DTCompilerUtil.tagDebug(indent, codeout, tag)
        args=DTUtil.tagCall(tag, [('until', 'None'), ('duration', 'None')])
        if args['until'] == 'None' and args['duration']=='None':
            raise DTExcept.DTCompileError ( tag, 
                  'must supply either until or duration argument' )
	args=DTCompilerUtil.pyifyArgs(tag, args)
        tempsecs=DTCompilerUtil.getTempName()
        if args['until'] != None:
            codeout.write(indent, '%s = __h.TimeUtil.convertUntil(%s)'
                          % (tempsecs, args['until']))
        elif args['duration'] != None:
            codeout.write(indent, '%s = __h.TimeUtil.convertDuration(%s)' % 
                          (tempsecs, args['duration']))
        codeout.write(indent, '__expiration = %s' % tempsecs)
        ttupv=DTCompilerUtil.getTempName()
        codeout.write(indent, '%s = __h.time.localtime(%s)' % (ttupv, tempsecs))
        codeout.write(indent, '__h.OUTPUT.write("<!-- cache expires:" + '
                              '__h.time.asctime(%s) + "-->")'  % ttupv)
        codeout.write(indent, 'del %s, %s' % (ttupv, tempsecs))
