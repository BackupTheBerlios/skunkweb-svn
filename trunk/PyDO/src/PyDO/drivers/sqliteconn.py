"""
PyDO driver for sqlite, using the pysqlite adapter.

Currently this has been tested with sqlite 2 (not sqlite 3), and
pysqlite 1.0.1.

"""


from PyDO.dbi import DBIBase
from PyDO.field import Field
from PyDO.exceptions import PyDOError

import sqlite

class SqliteDBI(DBIBase):
    # sqlite uses an auto increment approach to sequences
    auto_increment=True

    def _connect(self):
        return sqlite.connect(**self.connectArgs)

    def getAutoIncrement(self, name):
        return self.conn.db.sqlite_last_insert_rowid()

    def listTables(self, schema=None):
        """list the tables in the database schema.
        The schema parameter is not supported by this driver.
        """
        if schema is not None:
            raise ValueError, "db schemas not supported by sqlite driver"
        sql="SELECT name FROM sqlite_master WHERE type='table' ORDER BY NAME"
        c=self.conn.cursor()
        c.execute(sql)
        res=c.fetchall()
        if res:
            return tuple([x[0] for x in res])
        return ()



