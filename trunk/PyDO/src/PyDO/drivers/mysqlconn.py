"""
PyDO driver for MySQL, using the MySQLdb driver.

"""

from PyDO.dbi import DBIBase, ConnectionPool
from PyDO.exceptions import PyDOError
from PyDO.operators import BindingConverter
from PyDO.dbtypes import DATE, TIMESTAMP, BINARY, INTERVAL

import MySQLdb

class MysqlConverter(BindingConverter):
    converters={DATE: lambda x: x.value,
                TIMESTAMP: lambda x: x.value,
                BINARY: lambda x: x.value,
                INTERVAL: lambda x: x.value}

class MysqlDBI(DBIBase):
    auto_increment=True
    def __init__(self, connectArgs, pool=None, verbose=False):
        if pool and not hasattr(pool, 'connect'):
            pool=ConnectionPool()
        super(MysqlDBI, self).__init__(connectArgs, MySQLdb.connect, pool, verbose)
    
    def getAutoIncrement(self, name):
        try:
            return self.conn.insert_id()
        except AttributeError:
            raise PyDOError, "could not get insert id!"

    def getConverter(self):
        return MysqlConverter(self.paramstyle)
