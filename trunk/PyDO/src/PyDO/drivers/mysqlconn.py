"""
PyDO driver for MySQL, using the MySQLdb driver.

"""

from PyDO.dbi import DBIBase, ConnectionPool
from PyDO.exceptions import PyDOError

import MySQLdb

class MysqlDBI(DBIBase):

    def __init__(self, connectArgs, pool=None, verbose=False):
        if pool and not hasattr(pool, 'connect'):
            pool=ConnectionPool()
        super(MysqlDBI, self).__init__(connectArgs, MySQLdb.connect, pool, verbose)
    
    def getAutoIncrement(self, name):
        try:
            return self.conn.insert_id()
        except AttributeError:
            raise PyDOError, "could not get insert id!"
