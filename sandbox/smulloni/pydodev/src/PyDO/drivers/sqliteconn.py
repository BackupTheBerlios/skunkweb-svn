from PyDO.dbi import DBIBase

import sqlite

class SqliteDBI(DBIBase):

    def _connect(self):
        self.conn=sqlite.Connect(**self.connectArgs)

    def getAutoIncrement(self, name):
        return self.conn.db.sqlite_last_insert_rowid()

    
