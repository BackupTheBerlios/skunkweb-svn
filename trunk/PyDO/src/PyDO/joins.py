"""

The joins module contains a Join class that enables you to get
multiple PyDO objects in one join operation.

N.B.: this is still experimental!  And in any case, not every database
system will necessarily support every join, and this won't attempt to
deal with that, except by documenting what the limits are.

Current limits:

   * does not support nested joins.
   * does not support self joins.

"""

from PyDO.operators import SQLOperator, AND
from PyDO.utils import every
from PyDO.log import debug

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

class joinbase(object):
    """
    a class which joins two tables in a SQL92 join.
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

        # to support nesting of joins in the future ....
        self.connectionAlias=objL.connectionAlias
        self.jointype=jointype
        self.objL=objL
        self.objR=objR
        self.on=on
        self.using=using
        # rather than recalculating this all the time,
        # do it upon initialization        
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


    def getColumns(self, qualifier=None):
        # qualifier argument doesn't work or make sense at the moment
        return self.objL.getColumns(True) \
               + self.objR.getColumns(True)

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
        if conn.verbose:
            debug("SQL: %s", query)
            debug("bind variables: %s", values)
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

class CrossJoin(joinbase):
    def __init__(self, objL, objR):
        super(CrossJoin, self).__init__(objL, objR, 'CROSS')

class LeftJoin(joinbase):
    def __init__(self, objL, objR, on=None, using=None):
        super(LeftJoin, self).__init__(objL, objR, 'LEFT OUTER', on=on, using=using)

class NaturalLeftJoin(joinbase):
    def __init__(self, objL, objR):
        super(NaturalLeftJoin, self).__init__(objL, objR, 'NATURAL LEFT OUTER')

class RightJoin(joinbase):
    def __init__(self, objL, objR, on=None, using=None):
        super(RightJoin, self).__init__(objL, objR, 'RIGHT OUTER', on=on, using=using)

class NaturalRightJoin(joinbase):
    def __init__(self, objL, objR):
        super(NaturalRightJoin, self).__init__(objL, objR, 'NATURAL RIGHT OUTER')

class FullJoin(joinbase):
    def __init__(self, objL, objR, on=None, using=None):
        super(FullJoin, self).__init__(objL, objR, 'FULL OUTER', on=on, using=using)

class NaturalFullJoin(joinbase):
    def __init__(self, objL, objR):
        super(NaturalFullJoin, self).__init__(objL, objR, 'NATURAL FULL OUTER')

class InnerJoin(joinbase):
    def __init__(self, objL, objR, on=None, using=None):
        super(InnerJoin, self).__init__(objL, objR, 'INNER', on=on, using=using)

class NaturalInnerJoin(joinbase):
    def __init__(self, objL, objR):
        super(NaturalInnerJoin, self).__init__(objL, objR, 'NATURAL INNER')        


LeftOuterJoin=LeftJoin
NaturalLeftOuterJoin=NaturalLeftJoin
RightOuterJoin=RightJoin
NaturalRightOuterJoin=NaturalRightJoin
FullOuterJoin=FullJoin
NaturalFullOuterJoin=NaturalFullJoin
NaturalJoin=NaturalInnerJoin


__all__=['CrossJoin',
         'LeftJoin',
         'NaturalLeftJoin',
         'RightJoin',
         'NaturalRightJoin',
         'FullJoin',
         'NaturalFullJoin',
         'InnerJoin',
         'NaturalInnerJoin',
         'LeftOuterJoin',
         'NaturalLeftOuterJoin',
         'RightOuterJoin',
         'NaturalRightOuterJoin',
         'FullOuterJoin',
         'NaturalFullOuterJoin',
         'NaturalJoin']




