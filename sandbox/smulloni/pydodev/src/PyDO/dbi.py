from itertools import izip

from PyDO.log import *
from PyDO.operators import BindingConverter

class DBIBase(object):
    """base class for db connection wrappers"""
    paramstyle='format'
    autocommit=False
    
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

    def execute(self, sql, values=(), fields=()):
        """Executes the statement with the values and does conversion
        of the return result as necessary.
        result is list of dictionaries, or number of rows affected"""
        if self.verbose:
            debug("SQL: %s", (sql,))
            debug("bind variables: %s", (values,))

        c=self.conn.cursor()
        if values:
            c.execute(sql, values)
        else:
            # I don't want to assume that all drivers will like None,
            # or (), or {}, equally when there are no bind variables
            c.execute(sql)
        resultset=cur.fetchall()
        if not resultset:
            return cur.rowcount
        res=self._convertResultSet(cur.description, resultset)
        c.close()
        return res

    def _convertResultSet(description, resultset):
        """internal function that turns a result set into a list of dictionaries."""
        fldnames=[x[0] for x in description]
        return [dict(izip(fldnames, row)) for row in resultset]
    _convertResultSet=staticmethod(_convertResultSet)

    def getSequence(self, name):
        """If db has sequences, this should return the sequence named name"""
        pass

    def getAutoIncrement(self, name):
        """if things like mysql where can get the sequence after the insert"""
        pass

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
        driver=_get_driver(driver)
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
             
def InitAlias(alias, driver, connectArgs, cache=False, verbose=False):
    """initializes a connection alias with the stated connection arguments."""
    
    # I find that it can cause confusion to let this be called
    # repeatedly; you might think you are initializing it one way and
    # not realize it is being initialized elsewhere differently.  So
    # I'm raising a BooBoo if it is already initialized.
    
    if _aliases.has_key(alias):
        raise ValueError, "already initialized: %s" % alias
    _aliases[alias]=dict(driver=driver,
                         connectArgs=connectArgs,
                         cache=cache,
                         verbose=verbose)

def GetConnection(alias):
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
