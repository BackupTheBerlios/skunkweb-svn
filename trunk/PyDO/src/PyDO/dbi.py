from itertools import izip

from PyDO.log import *
from PyDO.operators import BindingConverter

class DBIBase(object):
    """base class for db connection wrappers"""
    paramstyle='format'
    autocommit=False
    # default to postgresql style for sequences,
    # out of sheer postgresql bigotry. 
    auto_increment=False
    
    def __init__(self, connectArgs, cache=False, verbose=False):
        self.cache=cache
        self.verbose=verbose
        self.connectArgs=connectArgs
        self.conn=self._connect()
        
    def commit(self):
        """commits a transaction"""
        self.conn.commit()

    def rollback(self):
        """rolls back a transaction"""
        self.conn.rollback()

    def cursor(self):
        return self.conn.cursor()

    def _connect(self):
        raise NotImplementedError

    def getConverter(self):
        """returns a converter instance."""
        return BindingConverter(self.paramstyle)

    def execute(self, sql, values=(), qualified=False):
        """Executes the statement with the values and does conversion
        of the return result as necessary.
        result is list of dictionaries, or number of rows affected"""
        if self.verbose:
            debug("SQL: %s", sql)
            debug("bind variables: %s", values)

        c=self.conn.cursor()
        if values:
            c.execute(sql, values)
        else:
            # I don't want to assume that all drivers will like None,
            # or (), or {}, equally when there are no bind variables
            c.execute(sql)
        resultset=c.fetchall()
        if not resultset:
            return c.rowcount
        res=self._convertResultSet(c.description, resultset, qualified)
        c.close()
        return res

    def _convertResultSet(description, resultset, qualified=False):
        """internal function that turns a result set into a list of dictionaries."""
        if qualified:
            fldnames=[x[0] for x in description]
        else:
            fldnames=[_strip_tablename(x[0]) for x in description]
        return [dict(izip(fldnames, row)) for row in resultset]
    _convertResultSet=staticmethod(_convertResultSet)

    def orderByString(order, limit, offset):
        def do_order(o):
            if isinstance(o, str):
                return o
            return ' '.join(o)
        if not order:
            order=""
        elif not isinstance(order, str):
            order= ', '.join(map(do_order, order))
        if order:
            order="ORDER BY %s" % order
        if limit not in ("", None):
            limit="LIMIT %s" % limit
        else:
            limit=""
        if offset not in ("", None):
            offset="OFFSET %s" % offset
        else:
            offset=""
        return " ".join(filter(None, (order, limit, offset)))
    orderByString=staticmethod(orderByString)

    def getSequence(self, name):
        """If db has sequences, this should return the next value of the sequence named 'name'"""
        pass

    def getAutoIncrement(self, name):
        """If db uses auto increment, should obtain the value of the auto-incremented field named 'name'"""
        pass

    def listTables(self, schema=None):
        """list the tables in the database schema"""
        raise NotImplementedError

    def describeTable(self, table):
        """returns a table description for the given table.
        The description is a 3-tuple of fields, unique constraints,
        and sequences/auto_increment for the table in question"""
        raise NotImplementedError

def _strip_tablename(colname):
    i=colname.rfind('.')
    if i==-1:
        return colname
    return colname[i+1:]

_driverConfig = {
    'mysql':       'PyDO.drivers.mysqlconn.MysqlDBI',
    'psycopg':	   'PyDO.drivers.psycopgconn.PsycopgDBI',
    'sqlite':      'PyDO.drivers.sqliteconn.SqliteDBI'
    # more to come!
    }
_loadedDrivers = {}
_aliases= {}

def _connect(driver, connectArgs, cache, verbose):
    if isinstance(driver, str):
        driver=_get_driver_class(driver)
    return driver(connectArgs, cache, verbose)

def _import_a_class(fqcn):
    lastDot=fqcn.rfind('.')   
    if lastDot==0:
        raise ValueError, "unable to import %s" %fqcn
    if lastDot>0:
        modName=fqcn[:lastDot]
        className=fqcn[lastDot+1:]
        try:
            module=__import__(modName, globals(), locals(), [className])
            return getattr(module, className)
        except (ImportError, AttributeError):
            raise ValueError, "impossible to import: %s" % fqcn
    else:
        raise ValueError, "impossible to import: %s" % fqcn

def _get_driver_class(name):
    if not _loadedDrivers.has_key(name):
        fqcn = _driverConfig[name]
        cls=_import_a_class(fqcn)
        _loadedDrivers[name] = cls
        return cls
    return _loadedDrivers[name]
             
def initAlias(alias, driver, connectArgs, cache=False, verbose=False):
    """initializes a connection alias with the stated connection arguments.
    
    It can cause confusion to let this be called repeatedly; you might
    think you are initializing it one way and not realize it is being
    initialized elsewhere differently.  Therefore, this raises a
    ValueError if the alias is already initialized with different
    data.  Multiple initializations with the same data (such as
    happens when a module calling initAlias is reloaded) are permitted.

    If you need to change the connect values at runtime, call delAlias
    before initAlias.
    
    """
    data=dict(driver=driver,
              connectArgs=connectArgs,
              cache=cache,
              verbose=verbose)
    old=_aliases.get(alias)
    if old and data!=old:
        raise ValueError, "already initialized: %s" % alias
    _aliases[alias]=data


def delAlias(alias):
    if _aliases.has_key(alias):
        del _aliases[alias]


def getConnection(alias):
    """get a connection given a connection alias"""
    try:
        conndata=_aliases[alias]
    except KeyError:
        raise ValueError, "alias %s not recognized" % alias
    if not conndata.has_key('connection'):
        res=_connect(**conndata)
        conndata['connection']=res
        return res
    return conndata['connection']


__all__=['initAlias', 'delAlias', 'getConnection']
