"""

The joins module contains a Join class that enables you to get
multiple PyDO objects in one join operation.

N.B.: this is a sketch -- it doesn't work yet!

"""

from PyDO.operators import SQLOperator, AND
from PyDO.utils import _strip_tablename

from itertools import izip

class Join(object):
    """
    """

    LEFT=LEFT_OUTER = 'LEFT OUTER'
    NATURAL_LEFT = NATURAL_LEFT_OUTER = 'NATURAL LEFT OUTER'
    RIGHT = RIGHT_OUTER = 'RIGHT OUTER'
    NATURAL_RIGHT = NATURAL_RIGHT_OUTER = 'NATURAL RIGHT OUTER'
    FULL = FULL_OUTER = 'FULL OUTER'
    NATURAL_FULL = NATURAL_FULL_OUTER = 'NATURAL FULL OUTER'
    INNER = 'INNER'
    NATURAL = NATURAL_INNER = 'NATURAL INNER'
    CROSS = 'CROSS'
    
    all_jointypes=(LEFT, NATURAL_LEFT, RIGHT, NATURAL_RIGHT,
                   FULL, NATURAL_FULL, INNER, NATURAL, CROSS)

    def __init__(self,
                 objL,
                 objR,
                 jointype=None,
                 on=None,
                 using=None):
        """

        """
        
        if jointype is None:
            if on is None and using is None:
                jointype=Join.CROSS
            else:
                jointype=Join.INNER
        else:
            # in case the string is passed in
            jointype=jointype.upper()
            if not jointype in Join.all_jointypes:
                raise ValueError, "unsupported join type: %s" % jointype
            if jointype.startswith('NATURAL'):
                if on or using:
                    raise ValueError, \
                          'cannot use "on" or "using" parameter with a natural join'
            else:
                if jointype!='CROSS' and not (on or using):
                    raise ValueError, \
                          'must define "on" or "using" parameter with this join'

        if objL.connectionAlias != objR.connectionAlias:
            raise ValueError, \
                  "connection aliases must the same for joined PyDO objects!"

        self.jointype=jointype
        self.objL=objL
        self.objR=objR
        self.on=on
        self.using=using


    def getDBI(self):
        return self.objL.getDBI()

    def _convertOn(self):
        # precondition: self.on is something        
        on=self.on
        assert on
        if isinstance(on, basestring):
            sql, vals=on, []
        elif isinstance(on, SQLOperator):
            converter=self.getDBI().getConverter()
            on.converter=converter
            sql=repr(on)
            vals=converter.values
        elif isinstance(on, (tuple, list)):
            if isinstance(on[0], basestring):
                sql,vals= on[0], on[1:]
            else:
                # should be SQLOperators
                converter=self.getDBI().getConverter()
                if len(on)==1:
                    on[0].converter=converter
                    sql=repr(on[0])
                    vals=converter.values
                else:
                    sql=repr(AND(converter=converter, *on))
                    vals= converter.values
        else:
            raise ValueError, "unsupported type for ON: %s" % type(on)
        return " ON (%s)" % sql, vals

    def _convertUsing(self):
        using=self.using
        # what is acceptable here? just a list of fieldnames, no?
        return ' USING (%s)' % ' ,'.join(using)
        

    def _baseSelect(self):
        fieldlist=', '.join(self.getColumns())
        if self.on:
            cond, vals=self._convertOn()
        elif self.using:
            cond, vals=self._convertUsing()
        else:
            cond=''
            vals=[]
        oL=self.objL
        oR=self.objR
        if oL.table==oR.table:
            # special case, but this doesn't work too well, actually
            # BROKEN
            t1="%s AS TL" % oL.table
            t2="%s AS TR" % oR.table
        else:
            t1=oL.table
            t2=oR.table
        join='%s %s JOIN %s%s' % (t1,
                                  self.jointype,
                                  t2,
                                  cond)
        select=['SELECT',
                fieldlist,
                'FROM',
                join]
        return ' '.join(select)


    def getColumns(self, qL=True, qR=True):
        return self.objL.getColumns(qL) + self.objR.getColumns(qR)

    def getSome(self, *args, **fieldData):
        """
        """
        order=fieldData.pop('order', None)
        limit=fieldData.pop('limit', None)
        offset=fieldData.pop('offset', None)
        conn=self.getDBI()
        sql, values=self.objL._processWhere(conn, args, fieldData)
        query=[self._baseSelect()]
        if sql:
            query.extend(['WHERE', sql])
        if filter(None, (order, limit, offset)):
            query.append(conn.orderByString(order, limit, offset))
        query=' '.join(query)
        result=conn.execute(query, values, True)
        if not result:
            return ()
        ret=[]
        for row in result:
            retrow=[]
            for o in (self.objL, self.objR):
                d=dict((_strip_tablename(c), row[c]) for c in o.getColumns(True))
                # if all values are NULL, take that as meaning that this
                # is a full or outer join and the whole object is NULL, and append
                # None
                for v in d.itervalues():
                    if v is not None:
                        notnull=True
                        break
                else:
                    notnull=False
                if notnull:
                    retrow.append(o(**d))
                else:
                    retrow.append(None)
            ret.append(tuple(retrow))
        return tuple(ret)
    
        
            
# classes that curry the constructor by jointype....

"""
column will either be

  alias.colname

or

  colname

if natural join, colnames will be unique -- I believe the alias will
go away.  So values could be found by position.  But since we'll be
explicitly stating all the columns we want, the column labels just
don't matter; we need to associate column with value by position in
the result set, not by name.  The same works also for the other joins.

Getting joins to nest is another problem...

"""
