import re

from PyDO.dbi import DBIBase
from PyDO.field import Field
from PyDO.exceptions import PyDOError

import sqlite

_createPat=re.compile(r'\((.*)\)', re.DOTALL)

class SqliteDBI(DBIBase):

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

    def describeTable(self, table):
        # fields
        # unique indices
        # auto_increment
        sql="SELECT sql FROM sqlite_master WHERE type='table' AND name='%s'" % table
        c=self.conn.cursor()
        c.execute(sql)
        res=c.fetchone()
        if not res:
            raise ValueError, "table not found"
        createSql=res[0]
        fields, auto_increment=self._parse_create_sql(createSql)
        return fields, (), auto_increment

    def _parse_create_sql(sql):
        m=_createPat.search(sql)
        if m:
            fields=[x.strip() for x in m.group(1).split(',')]
            fields=[x.split(' ',2) for x in fields]

            for f in fields:
                try:
                    name, dbtype, rest=f
                except ValueError:
                    continue
                else:
                    if dbtype.lower() in ('int', 'integer') \
                           and 'primary key' in rest.lower():
                        auto_increment=(name,)
                        break
            else:
                auto_increment=()
            return [Field(*x) for x in fields], auto_increment
        else:
            raise PyDOError, "could not parse create table sql: %s" % sql
    _parse_create_sql=staticmethod(_parse_create_sql)

        
