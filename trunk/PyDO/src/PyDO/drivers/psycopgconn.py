"""
PyDO driver for PostgreSQL, using the psycopg driver.

Currently this has been tested with psycopg 1.1.18 and 1.99.1.12,
and attempts to support both.

"""

from PyDO.dbi import DBIBase, ConnectionPool
from PyDO.exceptions import PyDOError
from PyDO.log import debug
from PyDO.operators import BindingConverter
from PyDO.dbtypes import DATE, TIMESTAMP, BINARY, INTERVAL, \
     date_formats, timestamp_formats

import time
import datetime

import psycopg

if psycopg.__version__[:3] >= '1.9':
   #psycopg version two.
   psycopg_version=2
else:
   psycopg_version=1

try:
   import mx.DateTime
   havemx=True
except ImportError:
   havemx=False
    
if havemx:
   try:
      from psycopg import TimestampFromMx
   except:
      assert psycopg_version==2
      def TimestampFromMx(x):
         return psycopg.TimestampFromTicks(x.ticks())
elif psycopg_version==1:
   raise ImportError, "mx.DateTime required when using psycopg version 1"

def convert_DATE(dt):
   val=dt.value
   if havemx and isinstance(val, mx.DateTime.DateTimeType):
      return psycopg.DateFromMx(val)
   elif isinstance(val, datetime.date):
      return psycopg.Date(dt.year, dt.month, dt.day)
   elif isinstance(val, (int, float, long)):
      d=datetime.date.fromtimestamp(val)
      return psycopg.Date(d.year, d.month, d.day)
   elif isinstance(val, (tuple, list)):
      return psycopg.Date(*val[:3])
   elif isinstance(val, (str, unicode)):
      for f in date_formats:
         try:
            t=time.strptime(val, f)[:3]
         except ValueError:
            continue
         else:
            return psycopg.Date(*t)
      else:
         raise ValueError, "cannot parse date format: '%s'" % val
   raise ValueError, val
    

def convert_TIMESTAMP(ts):
   val=ts.value
   if havemx and isinstance(val, mx.DateTime.DateTimeType):
      return TimestampFromMx(val)
   elif isinstance(val, datetime.datetime):
      return psycopg.TimestampFromTicks(time.mktime(ts.timetuple()))
   elif isinstance(val, (int, float, long)):
      return psycopg.TimestampFromTicks(val)
   elif isinstance(val, (tuple, list)) and len(val)==9:
      return psycopg.TimestampFromTicks(time.mktime(val))
   elif isinstance(val, (str, unicode)):
      for f in timestamp_formats:
         try:
            t=time.strptime(val, f)
         except ValueError:
            continue
         else:
            return psycopg.TimestampFromTicks(time.mktime(t))
      else:
         raise ValueError, "cannot parse timestamp format: '%s'" % val
   raise ValueError, val
    
_converters={datetime.datetime: lambda x: psycopg.TimestampFromTicks(time.mktime(x.timetuple())),
             datetime.date: lambda x: psycopg.Date(x.year, x.month, x.day),
             DATE: convert_DATE,
             TIMESTAMP: convert_TIMESTAMP,
             BINARY: lambda x: psycopg.Binary(x.value),
             INTERVAL: lambda x: x.value}

if havemx:
    # add automatic wrapping for mx.DateTime types
    _converters[mx.DateTime.DateTimeType]=TimestampFromMx
    _converters[mx.DateTime.DateTimeDeltaType]=lambda x: x.strftime("%d:%H:%M:%S")

class PsycopgConverter(BindingConverter): 
    converters=_converters

class PsycopgDBI(DBIBase):
    
    auto_increment=False

    def __init__(self, connectArgs, pool=None, verbose=False):
       if pool and not hasattr(pool, 'connect'):
          pool=ConnectionPool()
       super(PsycopgDBI, self).__init__(connectArgs, psycopg.connect, pool, verbose)
    
    def getConverter(self):
        return PsycopgConverter(self.paramstyle)
    
    def execute(self, sql, values=(), qualified=False):
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

    

