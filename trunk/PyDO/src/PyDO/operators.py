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

FIELD is a synonym for CONSTANT, a helper class which distinguishes
field names (and names of constants, like NULL) from plain strings,
which will appear in the SQL output as string literals.  NULL in
particular is available as a constant, due to the understandable
popularity of nullity; it is equal to CONSTANT('NULL').  Another
helper class, SET, is available to help use the IN operator:

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

SQLOperators can also take a conversion function that format data
values: SQLOperator(('EQ', FIELD('datecolumn'), myDate),
converter=myFunc).  Nested operators will inherit the conversion
function from the enclosing operator class if they don't define one
themselves.

The BindingConverter manages bind variables by inserting the
appropriate formats and accumulating the values inside the converter.

  >>> c=BindingConverter('format')
  >>> op=AND(OR(EQ(FIELD('x'),
  ...              FIELD('y')),
  ...           LT_EQ(FIELD('a'),
  ...                 MULT(FIELD('b'),
  ...                      EXP(FIELD('c'), 2)))),
  ...        IN(FIELD('e'), SET('Porthos', 'Athos', 'Aramis')), converter=c)
  >>> print op
  (((x = y) OR (a <= (b * (c ^ %s)))) AND (e IN (%s, %s, %s)))
  >>> c.values
  [2, 'Porthos', 'Athos', 'Aramis']
  >>> c.paramstyle='pyformat'
  >>> c.reset()
  >>> print op
  (((x = y) OR (a <= (b * (c ^ %(n1)s)))) AND (e IN (%(n2)s, %(n3)s, %(n4)s)))
  >>> c.values
  {'n1': 2, 'n2': 'Porthos', 'n3': 'Athos', 'n4': 'Aramis'}
  >>> c.paramstyle='numeric'
  >>> c.reset()
  >>> print op
  (((x = y) OR (a <= (b * (c ^ :1)))) AND (e IN (:2, :3, :4)))
  >>> c.values
  [2, 'Porthos', 'Athos', 'Aramis']
  >>> c.paramstyle='qmark'
  >>> c.reset()
  >>> print op
  (((x = y) OR (a <= (b * (c ^ ?)))) AND (e IN (?, ?, ?)))
  >>> c.values
  [2, 'Porthos', 'Athos', 'Aramis']
  >>> c.paramstyle='named'
  >>> c.reset()
  >>> print op
  (((x = y) OR (a <= (b * (c ^ :n1)))) AND (e IN (:n2, :n3, :n4)))
  >>> c.values
  {'n1': 2, 'n2': 'Porthos', 'n3': 'Athos', 'n4': 'Aramis'}
  
"""


__all__=['FIELD', 'CONSTANT', 'NULL', 'SET', 'SQLOperator', 'BindingConverter']

class CONSTANT(object):
    """a way to represent a constant or field name in a sql expression"""

    __slots__=('name',)
    
    def __init__(self, name):
        if not isinstance(name, str):
            raise TypeError, "name must be a string"
        self.name=name

    def __repr__(self):
        return self.name

NULL=CONSTANT('NULL')    
FIELD=CONSTANT

class SET(object):
    """a way of passing a set into PyDO where clauses (for IN), e.g.:
    
    >>> IN(FIELD('foo'), SET('spam', 'eggs', 'nougat'))
    (foo IN ('spam', 'eggs', 'nougat'))
    """
    __slots__=('values','converter')
    
    def __init__(self, *values):
        if not len(values):
            raise ValueError, "you must supply some values"
        self.values=tuple(values)
        self.converter=None

    def setConverter(self, converter):
        self.converter=converter
        for x in self.values:
            if hasattr(x, 'setConverter'):
                x.setConverter(converter)

    def _convert(self, val):
        if self.converter:
            return self.converter(val)
        # default converter is repr()
        return repr(val)
        
    def __repr__(self):
        l=len(self.values)
        if l>1:
            return "(%s)" % ', '.join([self._convert(x) for x in self.values])
        else:
            return "(%s)" % self._convert(self.values[0])


class SQLOperator(tuple):
    """A special kind of tuple that knows how to represent itself as a SQL string."""
    def __new__(cls, t, converter=None):
        if not (2 <= len(t)):
            raise ValueError, "invalid SQL condition"
        if not isinstance(t, SQLOperator):
            tl=[t[0]]
            for x in t[1:]:
                if isinstance(x, (SET, tuple)):
                    if not isinstance(x, (SET, SQLOperator)):
                        x=SQLOperator(x, converter)
                    else:
                        x.setConverter(converter)
                tl.append(x)
            t=tuple(tl)
        return tuple.__new__(cls, t)

    def __init__(self, t, converter=None):
        super(SQLOperator, self).__init__(t)
        # is this being done twice?
        self.setConverter(converter)

    def setConverter(self, converter):
        self.converter=converter
        for x in self:
            if hasattr(x, 'setConverter'):
                x.setConverter(converter)

    def _convert(self, val):
        if self.converter:
            return self.converter(val)
        # default converter is repr()
        return repr(val)
    
    def __repr__(self):
        op=" %s " % self[0]
        if len(self)==2:
            return "(%s %s)" % (op, self._convert(self[1]))
        args=[self._convert(a) for a in self[1:]]
        return "(%s)" % op.join(args)


class MonadicOperator(SQLOperator):
    def __new__(cls, val, converter=None):
        return SQLOperator.__new__(cls, (cls.operator, val), converter)
    def __init__(self, val, converter=None):
        super(MonadicOperator, self).__init__((self.__class__.operator, val), converter)
        
class DyadicOperator(SQLOperator):
    def __new__(cls, lval, rval, converter=None):
        return SQLOperator.__new__(cls, (cls.operator, lval, rval), converter)
            
    def __init__(self, lval, rval, converter=None):
        super(DyadicOperator, self).__init__((self.__class__.operator, lval, rval), converter)

class PolyadicOperator(SQLOperator):
    def __new__(cls, *values, **kw):
        if kw:
            converter=kw.get('converter')
            if not converter:
                raise ValueError, "converter is only keyword argument allowed"
        else:
            converter=None
        return SQLOperator.__new__(cls, (cls.operator,)+values, converter)
    
    def __init__(self, *values, **kw):
        if not values:
            raise ValueError, "some values required"
        if kw:
            converter=kw.get('converter')
            if not converter:
                raise ValueError, "converter is only keyword argument allowed"
        else:
            converter=None
        super(PolyadicOperator, self).__init__((self.__class__.operator,)+values, converter)


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
               ('REGEX', '~'),
               ('IREGEX', '~*'),
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


class BindingConverter(object):
    """A value converter that uses bind variables.
    
    >>> op=EQ(FIELD('x'), 45, converter=BindingConverter('format'))
    >>> print op
    (x = %s)
    >>> c=BindingConverter('format')
    >>> op=AND(EQ(FIELD('x'), 400), NE(FIELD('y'), ('^', FIELD('z'), 2)), converter=c)
    >>> type(op.converter)==BindingConverter
    True
    >>> type(op[1].converter)==BindingConverter
    True
    >>> type(op[2].converter)==BindingConverter
    True
    >>> type(op[2][2].converter)==BindingConverter
    True
    >>> print op
    ((x = %s) AND (y != (z ^ %s)))
    >>> c.values
    [400, 2]
    """
    supported_styles=('format', 'pyformat', 'qmark', 'named', 'numeric')

    def __init__(self, paramstyle):
        self._values=[]
        self._named_values={}
        self._seed=1
        self._set_paramstyle(paramstyle)

    def _get_paramstyle(self):
        return self._paramstyle

    def _set_paramstyle(self, paramstyle):
        if paramstyle not in BindingConverter.supported_styles:
            raise ValueError, "unsupported paramstyle: %s" % paramstyle
        self._paramstyle=paramstyle
        
    paramstyle=property(_get_paramstyle, _set_paramstyle)

    def values():
        def fget(self):
            p=self.paramstyle
            if p in ('format', 'qmark', 'numeric'):
                return self._values[:]
            elif p in ('pyformat', 'named'):
                return self._named_values.copy()
        return (fget,)
    values=property(*values())

    def _genName(self):
        return "n%d" % self._genNumber()

    def _genNumber(self):
        x=self._seed
        self._seed+=1
        return x

    def reset(self):
        self._seed=1
        del self._values[:]
        self._named_values.clear()

    def __call__(self, val):
        if val is None:
            return 'NULL'
        if isinstance(val, (CONSTANT, SET, SQLOperator)):
            return repr(val)
        elif self.paramstyle=='format':
            self._values.append(val)
            return '%s'
        elif self.paramstyle=='qmark':
            self._values.append(val)
            return '?'
        elif self.paramstyle=='numeric':
            self._values.append(val)
            return ":%d" % self._genNumber()
        elif self.paramstyle=='named':
            name=self._genName()
            self._named_values[name]=val
            return ":%s" % name
        elif self.paramstyle=='pyformat':
            name=self._genName()
            self._named_values[name]=val
            return "%%(%s)s" % name

if __name__=='__main__':
    import doctest
    doctest.testmod()
