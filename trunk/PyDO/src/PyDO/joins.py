"""

The joins module contains a Join class that enables you to get
multiple PyDO objects in one join operation.

N.B.: this is a sketch -- it doesn't work yet!

"""

from PyDO.operators import SQLOperator, AND
from PyDO.utils import every

from itertools import izip

all_jointypes=('LEFT',
               'LEFT OUTER',
               'NATURAL LEFT',
               'NATURAL LEFT OUTER',
               'RIGHT',
               'RIGHT OUTER',
               'NATURAL RIGHT',
               'NATURAL RIGHT OUTER',
               'FULL',
               'FULL OUTER',
               'NATURAL FULL',
               'NATURAL FULL OUTER',
               'INNER',
               'NATURAL',
               'NATURAL INNER',
               'CROSS')

class Join(object):
    """
    """

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
                jointype='CROSS'
            else:
                jointype='INNER'
        else:
            # in case the string is passed in
            jointype=jointype.upper()
            if not jointype in all_jointypes:
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
        cols=self.objL.getColumns(False)
        self._lenL=len(cols)
        self._allcols=cols+self.objR.getColumns(False)


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

    def _baseSelect(self):
        fieldlist=', '.join(self.getColumns())
        if self.on:
            cond, vals=self._convertOn()
        else:
            vals=[]
            if self.using:
                cond=' USING (%s)' % ', '.join(self.using)
            else:
                cond=''

        oL=self.objL
        oR=self.objR
        if oL.table==oR.table:
            # this won't work with nesting, but then, nothing will
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

    def _resolveObjects(self, resultRow):
        pairs=zip(self._allcols, resultRow)
        lenL=self._lenL
        dL, dR=map(dict, (pairs[:lenL], pairs[lenL:]))
        makeobj=lambda kls, d: (not every(None, d.itervalues())) and kls(**d) or None
        return makeobj(self.objL, dL), makeobj(self.objR, dR)


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
        if not every(None, (order, limit, offset)):
            query.append(conn.orderByString(order, limit, offset))
        query=' '.join(query)
        # we don't use the execute() method here, because we don't
        # want a dictionary, we need to know the order of columns in
        # the result set
        cursor=conn.cursor()
        cursor.execute(query, values)
        ret=[]
        while 1:
            row=cursor.fetchone()
            if row is None:
                break
            ret.append(self._resolveObjects(row))
        cursor.close()
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
This means that calling execute() isn't what we need, as it de-orders
the result.

Getting joins to nest is another problem, and I'll defer dealing with it.


"""
