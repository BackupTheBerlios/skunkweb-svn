from pydo.dbi import DBIBase, ConnectionPool
from pydo.exceptions import PyDOError
from pydo.operators import BindingConverter
from pydo.dbtypes import DATE, TIMESTAMP, BINARY, INTERVAL
from pydo.log import debug
from pydo.field import Field
from itertools import izip
import cx_Oracle

class OracleResultSet(object):
    """A resultset that for each row reads the content of any LOBs before 
    the LOB locators get invalidated by a subsequent fetch. To accommodate
    this, field access is mediated via an appropriate handler."""

    def __init__(self, cursor):
        self.cursor = cursor
        self.handlers = [self.get_handler(x[1]) for x in cursor.description]
    
    @staticmethod
    def get_handler(fieldtype):
        if fieldtype in (cx_Oracle.CLOB, cx_Oracle.BLOB, cx_Oracle.LOB):
            return lambda item: item.read()
        else:
            return lambda item: item

    def __iter__(self):
        return self
    
    def next(self):
        return [handler(item) for (item, handler) 
            in izip(self.cursor.next(), self.handlers)]
       
class OracleDBI(DBIBase):

    paramstyle = 'named'
    
    autocommit = None
    
    def __init__(self, connectArgs, pool=None, verbose=False):
       if pool and not hasattr(pool, 'connect'):
          pool = ConnectionPool()
       super(OracleDBI, self).__init__(connectArgs, cx_Oracle.connect, pool, verbose)

    def execute(self, sql, values=(), qualified=False):
        """Executes the statement with the values and does conversion
        of the return result as necessary.
        result is list of dictionaries, or number of rows affected"""
        if self.verbose:
            debug("SQL: %s", sql)
            debug("bind variables: %s", values)
        c = self.conn.cursor()
        if values:
            c.execute(sql, values)
        else:
            c.execute(sql)
        if c.description is None:
            resultset = None
        else:
            resultset = OracleResultSet(c)
        if not resultset:
            return c.rowcount
        res = self._convertResultSet(c.description, resultset, qualified)
        c.close()
        return res

    def getSequence(self, name):
        cur=self.conn.cursor()
        sql="select %s.nextval from dual" % name
        if self.verbose:
            debug("SQL: %s", (sql,))
        cur.execute(sql)
        res=cur.fetchone()
        if not res:
            raise PyDOError, "could not get value for sequence %s!" % name
        return res[0]

    def listTables(self, schema=None):
        """list the tables in the database schema"""
        raise NotImplementedError

    def describeTable(self, table, schema=None):
        """for the given table, returns a 2-tuple: a dict of Field objects
        keyed by name, and list of multi-column unique constraints (sets of Fields)).
        The Field instances should contain information about whether they are unique
        or sequenced.
        """
        raise NotImplementedError
