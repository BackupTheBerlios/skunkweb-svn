from PyDO.dbi import DBIBase
from PyDO.exceptions import PyDOError
from PyDO.log import debug
from psycopg import connect

class PsycopgDBI(DBIBase):
    
    auto_increment=False
    
    def _connect(self):
        return connect(self.connectArgs)


    def execute(self, sql, values=(), fields=(), qualified=False):
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
            c.execute(sql)
        if c.statusmessage=='SELECT':
            resultset=c.fetchall()
        else:
            resultset=None
        if not resultset:
            if c.statusmessage.startswith('INSERT') or c.statusmessage.startswith('UPDATE'):
                # rowcount doesn't work
                return int(c.statusmessage.split()[-1])
            return -1
        res=self._convertResultSet(c.description, resultset, qualified)
        c.close()
        return res    

    def getSequence(self, name):
        cur=self.conn.cursor()
        sql="select nextval('%s')" % name
        if self.verbose:
            debug("SQL: %s", (sql,))
        cur.execute(sql)
        res=cur.fetchone()
        if not res:
            raise PyDOError, "could not get value for sequence %s!" % name
        return res[0]

    
