from PyDO.dbi import DBIBase
from PyDO.exceptions import PyDOError

from psycopg import connect

class PsycopgDBI(DBIBase):
    
    def _connect(self):
        self.conn=psycopg.connect(self.connectArgs)

    def getSequence(self, name):
        cur=self.conn.cursor()
        sql="select nextval(%s)"
        values=(name,)
        if self.verbose:
            debug("SQL: %s", (sql,))
            debug("bind variables: %s", name)
        cur.execute(sql)
        res=cur.fetchone()
        if not res:
            raise PyDOError, "could not get value for sequence %s!" % name
        return res[0]

    
