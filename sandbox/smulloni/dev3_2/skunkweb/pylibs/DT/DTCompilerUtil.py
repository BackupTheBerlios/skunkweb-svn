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
# $Id$
########################################################################

import sys
import types
import string
import cStringIO
StringIO=cStringIO

import DTCommon
import DTParser
import DTExcept
from SkunkExcept import *

tempnum=0
cur_d=None

def getTempName():
    """generates temporary variable names"""
    global tempnum
    newname = '__t.temp%d' % tempnum
    # unlikely though it is, avoid overflow of int
    if tempnum < sys.maxint:
        tempnum += 1
    else:
        tempnum=0

    return newname

def tagDebug(indent, codeout, tag):
    """put some code to mark where we are in terms of execution"""
    codeout.write(indent, '__d.CURRENT_TAG = %s' % repr(repr(tag)))
    codeout.write(indent, '__d.CURRENT_LINENO = %s' % repr(tag.filelineno()))

def pyifyArgs(tag, args, parenthesize_exprs = 0):
    """convert arguments to an evalable format"""
    nd={}
    for k,v in args.items():
        if type(v)==types.StringType:
            if len(v)>1 and v[0]==v[-1]=="`":
                if parenthesize_exprs:
                    nd[k]="(%s)" % v[1:-1]
                else:
                    nd[k]=v[1:-1]
            else:
                nd[k]=repr(v)
        else:
            nd[k]=v

        if type(nd[k]) == types.StringType:
            try:
                compile(nd[k]+'\n', nd[k], 'exec')
            except SyntaxError, val:
                raise DTExcept.DTCompileError ( tag, 
                            'syntax error in argument: %s' % val)
    return nd

def pyifyKWArgs(tag, args, parenthesize_exprs = 0):
    nargs=pyifyArgs(tag, args, parenthesize_exprs)
    nl=[]
    for k,v in nargs.items():
        nl.append('%s: %s' % (repr(k),v))
    return '{'+string.join(nl,', ')+'}'

class Output:
    """the output object used for generating code"""
    def __init__(self):
        self.textlist=[]

    def write(self, indent, s):
        self.textlist.append((' '*indent) + s)

    def writemultiline(self, indent, s):
        it = ' '*indent
        for i in s.split('\n'):
            self.textlist.append(it + i)

    def getText(self):
        return string.join(self.textlist,'\n')+'\n'
    
    def writeOutObj(self, outObj):
        self.textlist.append(outObj.getText())

def niceifyStringOutput(indent, s):
    """break lines of long strings at 40 chars"""
    if not len(s):
        return '""'
    nl=[]
    lens=len(s)
    for i in range(0, lens, 40): #break lines at 40 chars
        if i+40 > lens:
            end=lens
        else:
            end=i+40
        nl.append(s[i:end])
    return string.join(map(repr, nl), '\n' + (indent*' '))

def genCodeNode(indent, codeout, tagreg, children, meta):
    for i in children:
        # XXX note that for now, we only generate meta data for top-level
        # tags!!!!
        genCodeChild(indent, codeout, tagreg, i, meta)

def genCodeChild ( indent, codeout, tagreg, thing, meta = None ):
    if type(thing) == types.StringType:
        # XXX experiment by Roman - do not write empty strings
        #
        # XXX commented back out, need to hack it later
        #if string.strip ( thing ):
        codeout.write(indent, '')
        codeout.write(indent, '########################################')
        codeout.write(indent, '__h.OUTPUT.write(%s)' %
                      niceifyStringOutput(indent+16, thing))
        codeout.write(indent, '########################################')
    elif (type(thing) == types.InstanceType
          and thing.__class__ == DTParser.Node):
        tagname=thing.children[0].tagname
        dttag=tagreg.getTag(tagname)

        # Generate the meta-data first
        if meta is not None:
            dttag.genMeta ( thing, meta )

        codeout.write(indent, '')
        codeout.write(indent, '#----------------------------------------')
        dttag.genCode(indent, codeout, tagreg, thing)
        codeout.write(indent, '#----------------------------------------')
    else: #an "empty" tag
        tagname=thing.tagname
        dttag=tagreg.getTag(tagname)

        # Generate the meta-data first
        dttag.genMeta ( thing, meta )

        codeout.write(indent, '')
        codeout.write(indent, '#----------------------------------------')
        dttag.genCode(indent, codeout, tagreg, thing)
        codeout.write(indent, '#----------------------------------------')

class dummy: pass

def setup_h ( cur_h ):
    """
    Add some variables to our hidden namespace
    """
    cur_h.NEWOUTPUT = StringIO.StringIO
    if not hasattr(cur_h, 'OUTPUT'):
        cur_h.OUTPUT = cur_h.NEWOUTPUT()

    if not hasattr ( cur_h, 'VALFMTRGY' ):
        cur_h.VALFMTRGY = DTCommon.ValFmtRgy

def get_d():
    global cur_d
    if cur_d is None:
        cur_d=dummy()
    return cur_d

def checkName(tag, argname, val, ppval = None):
    """
    tag is the tag which we are currently on
    argname is the tag argument name
    val is the val after pyifyArg*
    ppval is optional and is the val before pyifyArg*

    The reason for ppval is that it is possible for checkname to succeed
    on a val of `"foo bar"` and `"foo" + foo + "bar"`
    """
    if ppval and ppval[0]==ppval[-1]=='`':
        raise DTExcept.DTCompileError(tag, ('argument %s is an expression'
                                            ' and should be a string')
                                      % argname)
    if len(val) and (val[0]==val[-1]=='"' or val[0]==val[-1]=="'"):
        return val[1:-1]
    raise DTExcept.DTCompileError ( tag, ('argument %s is an expression and '
                                          'should be a string') % argname)

########################################################################
# $Log: DTCompilerUtil.py,v $
# Revision 1.1.1.1.2.1  2001/10/16 03:27:15  smulloni
# merged HEAD (basically 3.1.1) into dev3_2
#
# Revision 1.4  2001/09/21 21:07:14  drew_csillag
# now made
# it so that if you have a multi-line <:call:> tag, you don't have
# to have the ':> on it's own line for it to work.
#
# Revision 1.3  2001/09/21 20:36:08  drew_csillag
# fixed so print statements in templates now work
#
# Revision 1.2  2001/09/21 20:16:31  drew_csillag
# added userdir service (and subsidiary changes to other services) and multi-line ability for <:call:> tag
#
# Revision 1.1.1.1  2001/08/05 15:00:49  drew_csillag
# take 2 of import
#
#
# Revision 1.26  2001/07/09 20:38:41  drew
# added licence comments
#
# Revision 1.25  2001/04/12 22:05:33  smullyan
# added remote call capability to the STML component tag; some cosmetic changes.
#
########################################################################
