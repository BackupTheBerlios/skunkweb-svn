from itertools import izip
from threading import Lock
from marshal import dumps as marshal_dumps
from collections import deque

try:
    from threading import local
except ImportError:
    # threading goes out the window
    class local:
        pass
    
from PyDO.log import *
from PyDO.operators import BindingConverter
from PyDO.exceptions import PyDOError


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
        self._local=local()

    def conn():
        def fget(self):
            try:
                return self._local.connection
            except AttributeError:
                # vivify connection
                c=self._connect()
                self._local.connection=c
                return c

        def fset(self, c):
            self._local.connection=c

        def fdel(self):
            del self._local.connection
            
        return fget, fset, fdel, "the underlying db connection"
    conn=property(*conn())

    def swapConnection(self, connection):
        """switch the connection in use for a given thread with another one"""
        c=self._local.__dict__.get('connection')
        self._local.connection=connection
        return c
        
    def commit(self):
        """commits a transaction"""
        self.conn.commit()
        if self.cache:
            # return connection to cache
            del self.conn

    def rollback(self):
        """rolls back a transaction"""
        self.conn.rollback()
        if self.cache:
            # return connection to cache
            del self.conn

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
        if self.cache and self.autocommit:
            # return connection to pool
            del self.conn
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


class ConnectionWrapper(object):
    __slots__=('_conn', '_cache', '_args')
    
    def __init__(self, conn, args, cache):
        self._conn=conn
        self._args=args
        self._cache=cache
        
    def __getattr__(self, attr):
        return getattr(self._conn, attr)

    def __setattr__(self, attr, val):
        if attr in self.__slots__:
            super(ConnectionWrapper, self).__setattr__(attr, val)
        else:
            setattr(self._conn, attr, val)

    def close(self):
        # tell the cache that we are done and can be reused
        self._cache.release(self._conn, self._args)

    def __del__(self):
        self.close()


class ConnectionCache(object):
    
    """ a connection cache/pool """
    def __init__(self, max_poolsize=0, keep_poolsize=1, delay=0.2, retries=10):
        # deques of unused connections, keyed by serialized connection args
        self._free={}
        # lists of in-use connections, keyed by serialized connection args.
        # we need real references to these, not just a count.
        self._busy={}
        # maximum number of connections to create per connection args;
        # 0 or a negative value means no maximum
        self._max_poolsize=max_poolsize
        # maximum number of connections to keep alive per connection args
        self._keep_poolsize=keep_poolsize
        # time to sleep in seconds if max_poolsize connections are in
        # use before retrying
        self._delay=delay
        # number of times to retry in that case
        self._retries=10
        self._lock=Lock()

    def real_connect(self, connectArgs):
        raise NotImplementedError, "subclasses should implement this!"

    def connect(self, connectArgs):
        args=marshal_dumps(connectArgs)
        self._free.setdefault(args, deque())
        self._busy.setdefault(args, [])
        return self._connect(connectArgs,
                             args,
                             self._retries)

    def _connect(self, connectArgs, args, retries):
        """internal method; don't call it"""
        max_poolsize=self._max_poolsize
            
        self._lock.acquire()            
        try:
            # is there a connection available?
            free=self._free[args]
            busy=self._busy[args]
            if free:
                c=free.popleft()
                busy.append(c)
            else:
                lenbusy=len(busy)
                if max_poolsize>0:
                    # there is a cap on the number of connections
                    # we are allowed to create
                    assert lenbusy <= max_poolsize
                    if lenbusy==max_poolsize:
                        # can't create more, must retry or barf
                        if not retries:
                            # barf
                            raise PyDOError, \
                                  "all connections in use, number of retries: %d" % self._retries
                        else:
                            # retry, but get out of the mutex first
                            c=None
                    else:
                        # All are in use and we are allowed to create more.
                        # Do so.
                        c=self.real_connect(connectArgs)
                        busy.append(c)
                else:
                    # unlimited headroom, create new connection
                    c=self.real_connect(connectArgs)
                    busy.append(c)
        finally:
            self._lock.release()
        if c and self.onHandOut(c):
            return ConnectionWrapper(c, args, self)
        else:
            time.sleep(self._delay)             
            return self._connect(connectArgs, args, self._delay, retries-1)

    def release(self, conn, args):
        keep_poolsize=self._keep_poolsize
        self._lock.acquire()
        try:
            # do we keep this connection?
            free=self._free[args]
            busy=self._busy[args]
            numconns=len(free)+len(busy)
            keep=keep_poolsize<numconns
            busy.remove(conn)
            if keep:
                free.append(conn)
            self.onRelease(conn)
        finally:
            self._lock.release()

    def onRelease(self, realConn):
        """anything you want to do to a connection when it is returned"""
        pass

    def onHandOut(self, realConn):
        """any test you want to perform on a cached (i.e., not newly
        connected) connection before giving it out.  If the connection
        isn't good, return False"""
        return not realConn.closed
        


__all__=['initAlias',
         'delAlias',
         'getConnection',
         'ConnectionCache',
         'ConnectionWrapper']
