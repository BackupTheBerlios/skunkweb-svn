from pydo.dbi import DBIBase
from pydo.exceptions import PyDOError
from pydo.log import debug
from pydo.operators import BindingConverter
from psycopg import connect

import time
import datetime
try:
    import mx.DateTime
    havemx=True
except ImportError:
    havemx=False

_converters={}

def _init_converters():
    _converters[datetime.datetime]=lambda x: pyscopg.TimestampFromTicks(time.mktime(obj.timetuple))
    _converters[datetime.date]=lambda x: psycopg.Date(obj.year, obj.month, obj.day)
    if havemx:
        _converters[mx.DateTime.DateTimeType]=psycopg.TimestampFromMx

class PsycopgConverter(BindingConverter):
    def _wrapType(obj):
        converter=_converters.get(type(obj))
        if converter:
            return converter(obj)
        return obj
    _wrapType=staticmethod(_wrapType)

    def __call__(self, val):
        return super(PsycopgConverter, self).__call__(self._wrapType(val))

class PsycopgDBI(DBIBase):
    
    auto_increment=False
    
    def _connect(self):
        return connect(self.connectArgs)

    def getConverter(self):
        return PsycopgConverter(self.paramstyle)
    
    def execute(self, sql, values=(), fields=(), qualified=False):
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

    
