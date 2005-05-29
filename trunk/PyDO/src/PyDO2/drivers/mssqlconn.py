"""
PyDO driver for mssql, using the ADO adapter.
"""
from PyDO2.dbi import DBIBase, ConnectionPool
from PyDO2.field import Field, Sequence
from PyDO2.exceptions import PyDOError
from PyDO2.dbtypes import (DATE, TIMESTAMP, BINARY, INTERVAL,
                           date_formats, timestamp_formats)
from PyDO2.log import debug
from PyDO2.operators import BindingConverter

import time
import datetime

# do we actually need to import this, or is it optional? @@ TBD
import mx.DateTime

import adodbapi

def connection_string (server, database):
  return "Provider=SQLOLEDB;Data Source=%s;Initial Catalog=%s;Integrated Security=SSPI;" % (server, database)
  
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
   elif isinstance(val, basestring):
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
   elif isinstance(val, basestring):
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
             # removing BINARY, was using sqlite.Binary ... @@ FIX ME
             INTERVAL: lambda x: x.value}

class MssqlConverter(BindingConverter):
    converters=_converters


class MssqlDBI(DBIBase):
   auto_increment=True

   def __init__(self, connectArgs, pool=None, verbose=False):
      if pool and not hasattr(pool, 'connect'):
         pool=ConnectionPool()
      super(MssqlDBI, self).__init__(connectArgs, adodbapi.connect, pool, verbose)
      #
      # The DBI code seems to be looking for an
      #  autocommit attribute of the underlying
      #  db driver, even though the spec doesn't
      #  seem to suggest it's mandatory. Since
      #  I think SQL Server does do what the
      #  code is expecting from autocommit,
      #  turn the attribute on here.
      #
      self.conn.autocommit = True

   def getConverter(self):
      return MssqlConverter(self.paramstyle)

   def getAutoIncrement(self, name):
      q = self.conn.db.cursor ()
      q.execute ("SELECT @@IDENTITY")
      return q.fetchone ()[0]

   def listTables(self, schema=None):
      """list the tables in the database schema.
      """
      if schema:
        sql="""
          SELECT
            TABLE_NAME
          FROM
            INFORMATION_SCHEMA.TABLES
          WHERE
            TABLE_TYPE='BASE_TABLE' AND
            SCHEMA='%s'
          ORDER BY
            TABLE_NAME
        """ % schema
      else:
        sql="""
          SELECT
            TABLE_NAME
          FROM
            INFORMATION_SCHEMA.TABLES
          WHERE
            TABLE_TYPE='BASE_TABLE'
          ORDER BY
            TABLE_NAME
        """
      c=self.conn.cursor()
      c.execute(sql)
      res=c.fetchall()
      if res:
         return tuple(x[0] for x in res)
      return ()

   def describeTable(self, table, schema=None):
      schema = schema or 'dbo'
      fields={}
      unique=set()

      nullable=[]
      c=self.conn.cursor()

      if self.verbose:
         def execute(sql):
            debug('SQL: %s', (sql,))
            c.execute(sql)
      else:
         execute=c.execute

      sql = """
        select 
          COLUMN_NAME, 
          is_nullable = CASE LOWER (IS_NULLABLE) WHEN 'yes' THEN 1 ELSE 0 END,
          is_identity = COLUMNPROPERTY (OBJECT_ID (TABLE_SCHEMA + '.' + TABLE_NAME), COLUMN_NAME, 'IsIdentity')
        FROM
          INFORMATION_SCHEMA.COLUMNS
        WHERE
          TABLE_SCHEMA = '%s' AND
          TABLE_NAME = '%s'
      """ % (schema, table)
      execute (sql)
      for name, is_nullable, is_identity in c.fetchall ():
        if is_identity:
          #
          # @@FIXME: An identity doesn't have to be a PK. Is this implied?
          #
          fields[name] = Sequence (name)
        else:
          fields[name] = Field (name)
        if is_nullable:
          nullable.append (name)
        
      #
      # In theory this query should pull out unique constraints
      #  and unique indexes, but in practice it only pulls out
      #  the former.
      #
      constraint_sql = """
      SELECT
        tco.CONSTRAINT_CATALOG,
        tco.CONSTRAINT_SCHEMA,
        tco.CONSTRAINT_NAME
      FROM
        INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tco
      WHERE
        tco.TABLE_SCHEMA = '%s' AND
        tco.TABLE_NAME = '%s'
      AND
        tco.CONSTRAINT_TYPE IN ('UNIQUE', 'PRIMARY KEY')
      """ % (schema, table)
      column_sql = """
      SELECT
        ccu.COLUMN_NAME
      FROM
        INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu
      WHERE
        ccu.CONSTRAINT_CATALOG = '%s' AND
        ccu.CONSTRAINT_SCHEMA = '%s' AND
        ccu.CONSTRAINT_NAME = '%s'
      """
      execute (sql)
      for constraint_catalog, constraint_schema, constraint_name in c.fetchall ():
        q2 = self.conn.cursor ()
        q2.execute (column_sql % (constraint_catalog, constraint_schema, constraint_name))
        unique.add (frozenset ([r[0] for r in q2.fetchall ()]))
        
      #
      # The adodbapi driver complains if the sp_helpindex returns with
      #  no indexes, so make sure that there is at least one before
      #  trying.
      #
      sql = """
      SELECT * FROM sysindexes WHERE id = OBJECT_ID ('%s.%s') AND indid BETWEEN 1 AND 254
      """ % (schema, table)
      execute (sql)
      rows = c.fetchall ()
      print "rows=", rows
      if rows: # c.fetchall ():
        sql = "sp_helpindex '%s.%s'" % (schema, table)
        execute (sql)
        for index_name, index_description, index_keys in c.fetchall ():
          #
          # The description field from sp_helpindex contains an ill-defined
          #  set of descriptors, somewhere including the word "unique". The
          #  separators could be commas or spaces, or both.
          #
          descriptions = [d.strip () for d in index_description.lower ().replace (",", " ").split ()]
          if "unique" in descriptions:
            unique.add (frozenset ([k.strip () for k in index_keys.split (",")]))
      
      return fields, unique
