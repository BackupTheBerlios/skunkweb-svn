from PyDO2.base import PyDO
from PyDO2.log import debug
from PyDO2.utils import iflatten, _strip_tablename
from inspect import isclass
import string
from itertools import izip

class TableAlias(object):
    def __init__(self, obj, alias):
        self.obj=obj
        self.alias=alias
        self.connectionAlias=self.obj.connectionAlias

    def getAlias(self):
        return self.alias

    def getTable(self):
        return "%s %s" % (self.obj.getTable(), self.alias)

    def getColumns(self, alias=True):
        return self.obj.getColumns(self.alias)

    def getDBI(self):
        return self.obj.getDBI()

    def __call__(self, **kwargs):
        return self.obj(**kwargs)

def flattenResultSpec(resultSpec):
    for i in resultSpec:
        if isinstance(i, (list, tuple)):
            if len(i)==2 and isclass(i[0]) and isinstance(i[1], basestring):
                # an alias
                yield TableAlias(*i)
            else:
                for x in flattenResultSpec(i):
                    yield x
        else:
            if isclass(i):
                if not issubclass(i, PyDO):
                    raise ValueError, "unknown class"
            elif not isinstance(i, (TableAlias, basestring)):
                raise ValueError, "table alias or string expression: %s" % i
            yield i

def iterfetch(resultSpec, sqlTemplate, *values, **kwargs):
    """
    a method that executes sql and returns rows of tuples of PyDO
    objects and scalar values, ordered according to a result set
    specification.

    resultSpec is a list that may contain:

      * PyDO classes;
      
      * 2-tuples of (PyDO class, alias string), which indicate that
        the table represented by the PyDO class is to be referenced by
        the given alias;

      * strings, which represent arbitrary SQL expressions that may
        occur in a SQL column-list specification.

    The resultSpec list may contain nested lists, which will be
    flattened for you and are taken to be equivalent to an unflattened
    list (except for the 2-tuples mentioned above).

    sqlTemplate is a string that may contain interpolation variables
    in the style of string.Template.  In particular, two variables are
    supplied to this template automatically:

      $COLUMNS -- a list of columns computed from the supplied resultSpec;

      $TABLES -- a list of tables similarly computed.

    Additional interpolation variables may be passed in as keyword
    arguments.  Bind variables to the SQL may also be passed in,
    through positional arguments; if there is only one positional
    argument, and it is a dictionary, it will be used instead of a
    list of values, under the assumption that the 'pyformat'
    paramstyle is being used.

    For each element E in the (flattened) resultSpec, the result row
    contains one element F.  If E is a PyDO class, F will either be an
    instance of E, or, if all its corresponding columns were null for
    that row, None.  If E is a string, F will be whatever the cursor
    returned for that column.
    """
    resultSpec=list(flattenResultSpec(resultSpec))
    objs=[x for x in resultSpec if not isinstance(x, basestring)]
    # check that all objs have the same connectionAlias
    caliases=tuple(frozenset(o.connectionAlias for o in objs))
    if len(caliases)!=1:
        raise ValueError, \
              "objects passed to fetch must have same connection alias"
    dbi=objs[0].getDBI()    

    tables = ', '.join(x.getTable() for x in objs)
    allcols=[]
    for item in resultSpec:
        if hasattr(item, 'getColumns'):
            allcols.append(item.getColumns(True))
        else:
            allcols.append(item)
    columns=', '.join(iflatten(allcols))
    sql=string.Template(sqlTemplate).substitute(kwargs,
                                                TABLES=tables,
                                                COLUMNS=columns)
    c=dbi.cursor()
    if len(values)==1 and isinstance(values, dict):
        values=values[0]
    if dbi.verbose:
        debug('SQL: %s', sql)
        debug('bind variables: %s', values)
    c.execute(sql, values)
    result=c.fetchall()
    c.close()
    if not result:
        raise StopIteration
    retrow=[]
    for row in result:
        del retrow[:]
        p=0
        for o, cols in izip(resultSpec, allcols):
            if isinstance(o, basestring):
                retrow.append(row[p])
                p+=1
            else:
                assert isinstance(o, TableAlias) or (isclass(o) and issubclass(o, PyDO))
                d={}
                for col in cols:
                    d[_strip_tablename(col)]=row[p]
                    p+=1
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
        yield tuple(retrow)

def fetch(resultSpec, sqlTemplate, *values, **kwargs):
    return list(iterfetch(resultSpec, sqlTemplate, *values, **kwargs))

fetch.__doc__=iterfetch.__doc__

__all__=['fetch']
