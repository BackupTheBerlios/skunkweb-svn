from pydo.dbi import DBIBase
from pydo.exceptions import PyDOError

import MySQLdb

class MysqlDBI(DBIBase):
    auto_increment=True
    
    def _connect(self):
        return MySQLdb.connect(**self.connectArgs)

    def getAutoIncrement(self, name):
        try:
            return self.conn.insert_id()
        except AttributeError:
            raise PyDOError, "could not get insert id!"
