"""
PyDO driver for MySQL, using the MySQLdb driver.

"""

from PyDO2.dbi import DBIBase, ConnectionPool
from PyDO2.exceptions import PyDOError
from PyDO2.operators import BindingConverter
from PyDO2.dbtypes import DATE, TIMESTAMP, BINARY, INTERVAL
from PyDO2.field import Field, Unique, Sequence
from PyDO2.log import debug

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

    def listTables(self, schema=None):
        """ lists tables in the database."""
        sql="SHOW TABLES"
        cur=self.conn.cursor()
        if self.verbose:
            debug('SQL: %s', (sql,))
        cur.execute(sql)
        res=cur.fetchall()
        cur.close()
        if not res:
            return []
        return sorted(x[0] for x in res)

    def describeTable(self, table, schema=None):
        cur=self.conn.cursor()
        if self.verbose:
            def execute(sql):
                debug('SQL: %s', (sql,))
                cur.execute(sql)
        else:
            execute=cur.execute
            
        sql="SHOW TABLES LIKE '%s'" % table
        execute(sql)
        res=cur.fetchone()
        if not res:
            raise ValueError, "table %s not found" % table
        sql="SHOW COLUMNS FROM %s" % table
        execute(sql)
        res=cur.fetchall()
        fields={}
        for row in res:
            name, tipe, nullable, key, default, extra=row
            if extra=='auto_increment':
                fields[name]=Sequence(name)
#            elif (not nullable) and (key=='UNI' or key=='PRI'):
#                fields[name]=Unique(name)
            else:
                fields[name]=Field(name)
                
        sql="SHOW INDEX FROM %s" % table
        execute(sql)
        res=cur.fetchall()
        cur.close()
        indices={}
        blacklist=set()
        # columns we care about, and their index in the result set:
        # Non_unique:   1
        # Key_name:     2
        # Column_name : 4
        for row in res:
            keyname=row[2]
            colname=row[4]
            notunique=row[1]
            # if not a unique index, the whole index is tainted, don't use it
            if notunique:
                blacklist.add(keyname)
                continue
            if keyname in blacklist:
                continue
            # build dictionary of lists
            indices.setdefault(keyname, [])
            indices[keyname].append(colname)

        unique=set(frozenset(x) for x in indices.values())
        return fields, unique
            
