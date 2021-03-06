# $Id$
# Time-stamp: <01/09/11 00:12:05 smulloni>

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

class SQLOperator:
    def asTuple(self):
        """
        returns a lisp-like nested tuple representation of the operator and its
        arguments, included nested operators.  The tuple is of the form (symbol, *args)
        """
        _astuple=lambda val: (isinstance(val, SQLOperator) and val.asTuple()) or val
        lst=[self.__class__.symbol]
        for v in self.values:
            lst.append(_astuple(v))
        return tuple(lst)
    
    def asSQL(self, fieldDict=None, conn=None):
        """
        this performs no escaping, as we don't necessarily know what the field
        or its type is in this context.  However, the use of type-specifier input
        classes, like FIELD, could ameliorate the problem to a degree.
        """
 ##       _escape=(conn and fieldDict and lambda k, v, c=conn, f=fieldDict: \
##                 conn.sqlStringAndValue(v, k, f[k])[0]) or lambda k, v: str(v)
        _assql=lambda v: (isinstance(v, SQLOperator) and "(%s)" % v.asSQL()) \
                or (type(v)==type("") and "'%s'" % v) or str(v)
##        def _assql2(v):
##            if isinstance(v, SQLOperator):
##                if isinstance(v, DyadicOperator) or isinstance(v, PolyadicOperator):
##                    for val in v.values():
##                        if isinstance(val, FIELD):
##                            dbtype=fieldDict.get(val.fieldname)
        vallen=len(self.values)
        if vallen==1:            
            return "%s %s" % (self.__class__.symbol, _assql(self.values[0]))
        else:
            return (" %s " % self.__class__.symbol).join(map(_assql, self.values))

class MonadicOperator(SQLOperator):
    def __init__(self, val):
        self.values=(val,)
        
class DyadicOperator(SQLOperator):
    def __init__(self, lval, rval):
        self.values=(lval, rval)

class PolyadicOperator(SQLOperator):
    def __init__(self, *values):
        self.values=values

class FIELD:
    """
    a cheesy way of indicating that a string represents the name of a field, not a string literal
    """
    def __init__(self, fieldname):
        if type(fieldname)!=type(""):
            raise TypeError, "fieldname must be a string"
        self.fieldname=fieldname

    def __str__(self):
        return self.fieldname

"""
mapping of symbols to operator classes
"""
symbol_table={}

def tupleToSQL(optuple):
    """
    takes the tuple notation, as produced by SQLOperator.asTuple(),
    and translates it into SQL
    """
    _assql=lambda v: (type(v)==type(()) and "(%s)" % tupleToSQL(v)) \
            or (type(v)==type("") and "'%s'" % v) or str(v)
    lent=len(optuple)
    if lent<2:
        raise ValueError, "malformed input"
    if lent==2: # monadic
        return "%s %s" % (optuple[0], _assql(optuple[1:]))
    elif lent>2: #dyadic or better
        return (" %s " % optuple[0]).join(map(_assql, optuple[1:]))

def tupleToSQLOperator(optuple):
    """
    inverse operator of SQLOperator.asTuple()
    """
    lent=len(optuple)
    if lent<2:
        raise ValueError, "malformed input"    
    sym=optuple[0]
    kl=symbol_table.get(sym)
    if not kl:
        raise ValueError, "symbol %s not recognized" % sym
    arglist=map(lambda x: (type(x)==type(()) and tupleToSQLOperator(x)) or x, optuple[1:])
    return kl(*arglist)

def __makeOperators():
    """
    generates the operator classes;
    more need to be added, here are some obvious ones
    """
    import new
    _factory=(  (  MonadicOperator,
                   ('NOT', '!'),
                   ),
                (  DyadicOperator,
                   ('EQ', '='),
                   ('NE', '!='),
                   ('LT', '<'),
                   ('LT_EQ', '<='),
                   ('GT', '>'),
                   ('GT_EQ', '>='),
                   ('LIKE', 'LIKE'),
                   ),
                (  PolyadicOperator,
                   ('AND', 'AND'),
                   ('OR', 'OR'),
                   ('PLUS', '+'),
                   ('MINUS', '-'),
                   ('MULT', '*'),
                   ('DIV', '/'),
                   )
                )
    for tup in _factory:
        base=tup[0]
        for specs in tup[1:]:
            klname, sym=specs
            kl=new.classobj(klname, (base,), {})
            kl.symbol=sym
            globals()[klname]=kl
            symbol_table[sym]=kl


            
########################################################################
            
__makeOperators()
del __makeOperators
        

