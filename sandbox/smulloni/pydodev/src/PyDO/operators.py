""" This module permits a useful subset of SQL where clauses to be
defined with a Lispo-Pythonic syntax:

  >>> g=SQLOperator(('AND', ('LIKE', FIELD('username'), 'bilbo_bag%'),
  ...                       ('>', FIELD('x'), 40)))
  >>> print g
  ((username LIKE 'bilbo_bag%') AND (x > 40))

SQLOperator is a tuple subclass that represents itself as a SQL
string.  The first element of the tuple is the SQL operator, and the
remaining elements are arguments, which may be atoms or nested tuples,
which are recursively converted to SQLOperator tuples.

The FIELD class is a helper class which distinguishes field names (and
names of constants, like NULL) from plain strings, which will appear
in the SQL output as string literals.  NULL in particular is available
as a constant, due to the understandable popularity of nullity; it is
equal to FIELD('NULL').  Another helper class, SET, is available to
help use the IN operator:

  >>> print SQLOperator(('IN', FIELD('x'), SET(1, 2, 3, 4)))
  (x IN (1, 2, 3, 4))

For convenience, most SQL operators are additionally wrapped in
operator-specific SQLOperator subclasses, which are exactly equivalent
to the explicit tuple notation and are exactly equivalent:

  >>> print IN(FIELD('x'), SET(1, 2, 3, 4))
  (x IN (1, 2, 3, 4))
  >>> print AND(OR(EQ(FIELD('x'),
  ...                 FIELD('y')),
  ...              LT_EQ(FIELD('a'),
  ...                    MULT(FIELD('b'),
  ...                         EXP(FIELD('c'), 2)))),
  ...           IN(FIELD('e'), SET('Porthos', 'Athos', 'Aramis')))
  (((x = y) OR (a <= (b * (c ^ 2)))) AND (e IN ('Porthos', 'Athos', 'Aramis')))

"""


__all__=['FIELD', 'SET', 'SQLOperator', 'NULL']

class FIELD(object):
    """a way to represent a fieldname in a sql expression"""

    __slots__=('fieldname',)
    
    def __init__(self, fieldname):
        if not isinstance(fieldname, str):
            raise TypeError, "fieldname must be a string"
        self.fieldname=fieldname

    def __repr__(self):
        return self.fieldname

NULL=FIELD('NULL')    

class SET(object):
    """a way of passing a set into PyDO where clauses (for IN), e.g.:
    
    IN(FIELD('foo'), SET('spam', 'eggs', 'nougat'))
    """
    __slots__=('values',)
    
    def __init__(self, *values):
        if not len(values):
            raise ValueError, "you must supply some values"
        self.values=tuple(values)
        
    def __repr__(self):
        l=len(self.values)
        if l>1:
            return "(%s)" % ', '.join([repr(x) for x in self.values])
        else:
            return "(%r)" % self.values[0]


class SQLOperator(tuple):
    def __new__(cls, t):
        L=len(t)
        if not (2 <= L):
            raise ValueError, "invalid SQL condition"
        if not isinstance(t, SQLOperator):
            tl=[t[0]]
            for x in t[1:]:
                if isinstance(x, tuple):
                    if isinstance(x, SQLOperator):
                        tl.append(x)
                    else:
                        tl.append(SQLOperator(x))
                else:
                    tl.append(x)
            t=tuple(tl)
        return tuple.__new__(cls, t)

    
    def __repr__(self):
        L=len(self)
        if L==2:
            return "(%s %r)" % self
        op=" %s " % self[0]
        args=map(repr, self[1:])
        return "(%s)" % op.join(args)


class MonadicOperator(SQLOperator):
    def __new__(cls, val):
        return SQLOperator.__new__(cls, (cls.operator, val))
    def __init__(self, val):
        super(MonadicOperator, self).__init__(self, (self.__class__.operator, val))
        
class DyadicOperator(SQLOperator):
    def __new__(cls, lval, rval):
        return SQLOperator.__new__(cls, (cls.operator, lval, rval))
            
    def __init__(self, lval, rval):
        super(DyadicOperator, self).__init__(self, (self.__class__.operator, lval, rval))

class PolyadicOperator(SQLOperator):
    def __new__(cls, *values):
        return SQLOperator.__new__(cls, (cls.operator,)+values)
    
    def __init__(self, *values):
        super(PolyadicOperator, self).__init__(self, (self.__class__.operator,)+values)


def __makeOperators():
    """
    generates the operator classes;
    more need to be added, here are some obvious ones
    """
    import new
    _factory=((MonadicOperator,
               ('NOT', 'NOT'),
               ('ISNULL', 'ISNULL'),
               ('NOTNULL', 'NOTNULL')
               ),
              (DyadicOperator,
               ('EQ', '='),
               ('NE', '!='),
               ('LT', '<'),
               ('LT_EQ', '<='),
               ('GT', '>'),
               ('GT_EQ', '>='),
               ('MOD', '%'),
               ('EXP', '^'),
               ('LIKE', 'LIKE'),
               ('ILIKE', 'ILIKE'),
               ('SIMILAR', 'SIMILAR'),
               ('BETWEEN', 'BETWEEN'),
               ('OVERLAPS', 'OVERLAPS'),
               ('IN', 'IN'),
               ('IS', 'IS'),
               ),
              (PolyadicOperator,
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
            kl.operator=sym
            globals()[klname]=kl
            __all__.append(klname)


__makeOperators()
del __makeOperators

        

if __name__=='__main__':
    import doctest
    doctest.testmod()
