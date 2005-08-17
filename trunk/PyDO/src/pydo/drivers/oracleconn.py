from pydo.dbi import DBIBase, ConnectionPool
from pydo.exceptions import PyDOError
from pydo.operators import BindingConverter
from pydo.dbtypes import DATE, TIMESTAMP, BINARY, INTERVAL
from pydo.log import debug
from pydo.field import Field
import cx_Oracle

class OracleDBI(DBIBase):

    paramstyle = 'named'
    
    autocommit = None
    
    def __init__(self, connectArgs, pool=None, verbose=False, initFunc=None):
       if pool and not hasattr(pool, 'connect'):
          pool = ConnectionPool()
       super(OracleDBI, self).__init__(connectArgs,
                                       cx_Oracle.connect,
                                       cx_Oracle,
                                       pool,
                                       verbose,
                                       initFunc)

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
            lob_types = set((cx_Oracle.CLOB, cx_Oracle.BLOB))
            field_types = set(d[1] for d in c.description)
            have_lobs = field_types & lob_types
            if have_lobs:
                resultset = [list(self.field_values(row)) for row in c]
            else:
                resultset = c.fetchall()
        if not resultset:
            return c.rowcount
        res = self._convertResultSet(c.description, resultset, qualified)
        c.close()
        return res

    @staticmethod
    def field_values(row):
        """Produces the value of each item in the row, reading any LOBs before 
        the LOB locators get invalidated by a subsequent fetch."""
        for item in row:
            if hasattr(item, "read"):
                yield item.read()
            else:
                yield item
                
    def getSequence(self, name, field, table):
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
        """lists the tables in the database schema"""
        if schema is None:
            schema = 'PUBLIC'
        sql = """
            SELECT t.object_name
            FROM sys.all_objects t
            WHERE t.owner = :schema AND t.object_type IN ('TABLE', 'VIEW')
            """
        cur = self.conn.cursor()
        if self.verbose:
            debug("SQL: %s", (sql,))
        cur.execute(sql, schema=schema)
        res = cur.fetchall()
        cur.close()
        if not res:
            return []
        return sorted(x[0] for x in res)

    def describeTable(self, table, schema=None):
        """for the given table, returns a 2-tuple: a dict of Field objects
        keyed by name, and list of multi-column unique constraints (sets of Fields)).
        The Field instances should contain information about whether they are unique
        or sequenced.
        """
        raise NotImplementedError
