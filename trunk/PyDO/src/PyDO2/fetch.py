from PyDO2.base import PyDO
from PyDO2.log import debug
from PyDO2.utils import iflatten, stripTname
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
    sql=string.Template(sqlTemplate).substitute(kwargs, TABLES=tables, COLUMNS=columns)
    c=dbi.cursor()
    if dbi.verbose:
        debug('SQL: %s', sql)
        debug('bind variables: %s', values)
    c.execute(sql, values)
    result=c.fetchall()
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
                    d[stripTname(col)]=row[p]
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
