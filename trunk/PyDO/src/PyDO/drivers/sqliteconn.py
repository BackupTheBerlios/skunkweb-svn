"""
PyDO driver for sqlite, using the pysqlite adapter.

Currently this has been tested with sqlite 2 (not sqlite 3), and
pysqlite 1.0.1.

TODO: add support for sqlite3 and corresponding version of pysqlite.

"""


from PyDO.dbi import DBIBase, ConnectionCache
from PyDO.field import Field
from PyDO.exceptions import PyDOError
from PyDO.dbtypes import DATE, TIMESTAMP, BINARY, INTERVAL, \
     date_formats, timestamp_formats
from PyDO.operators import BindingConverter

import time
import datetime

import sqlite
# currently required for this version of pysqlite
import mx.DateTime


def convert_DATE(dt):
   val=dt.value
   if isinstance(val, mx.DateTime.DateTimeType):
      return val
   elif isinstance(val, datetime.date):
      return mx.DateTime.DateFrom(dt.year, dt.month, dt.day)
   elif isinstance(val, (int, float, long)):
      d=datetime.date.fromtimestamp(val)
      return mx.DateTime.DateFrom(d.year, d.month, d.day)
   elif isinstance(val, (tuple, list)):
      return mx.DateTime.DateFrom(*val[:3])
   elif isinstance(val, (str, unicode)):
      for f in date_formats:
         try:
            t=time.strptime(val, f)[:3]
         except ValueError:
            continue
         else:
            return mx.DateTime.DateFrom(*t)
      else:
         raise ValueError, "cannot parse date format: '%s'" % val
   raise ValueError, val

def convert_TIMESTAMP(ts):
   val=ts.value
   if isinstance(val, mx.DateTime.DateTimeType):
      return val
   elif isinstance(val, datetime.datetime):
      return mx.DateTime.DateTimeFromTicks(time.mktime(ts.timetuple()))
   elif isinstance(val, (int, float, long)):
      return mx.DateTime.DateTimeFromTicks(val)
   elif isinstance(val, (tuple, list)) and len(val)==9:
      return mx.DateTime.DateTimeFromTicks(time.mktime(val))
   elif isinstance(val, (str, unicode)):
      for f in timestamp_formats:
         try:
            return mx.DateTime.strptime(val, f)
         except ValueError:
            continue
      else:
         raise ValueError, "cannot parse timestamp format: '%s'" % val
   raise ValueError, val


_converters={datetime.datetime: lambda x: mx.DateTime.DateTimeFromTicks(time.mktime(x.timetuple())),
             datetime.date: lambda x: mx.DateTime.DateFromTicks(time.mktime(x.timetuple())),
             DATE: convert_DATE,
             TIMESTAMP: convert_TIMESTAMP,
             BINARY: lambda x: sqlite.Binary(x.value),
             INTERVAL: lambda x: x.value}

class SqliteConverter(BindingConverter):
    converters=_converters

class SqliteCache(ConnectionCache):
   def realConnect(self, connectArgs):
      return sqlite.connect(**connectArgs)

class SqliteDBI(DBIBase):
   # sqlite uses an auto increment approach to sequences
   auto_increment=True

   def __init__(self, connectArgs, cache=False, verbose=False):
      if cache and not hasattr(cache, 'connect'):
         cache=SqliteCache()
      super(SqliteDBI, self).__init__(connectArgs, cache, verbose)
   
   def getConverter(self):
      return SqliteConverter(self.paramstyle)

   def _connect(self):
      if self.cache:
         return cache.connect(self.connectArgs)
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



