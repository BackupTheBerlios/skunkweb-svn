#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
#   
import types
import Date
import DateTime
import string
from MySQL import MySQL
import PyDBI

class PyDOMySQL:
    def __init__(self, connectString):
        self.connectString = connectString
        bits = tuple(string.split(connectString, ':'))
        self.conn = apply(MySQL.connect, bits[1:4])
        if bits[-1] == 'verbose':
            self.verbose = 1
        else:
            self.verbose = 0
        self.conn.selectdb(bits[0])
        self.bindVariables = 0
    
    def getConnection(self): return self.conn

    def numberType(self, dbtype):
        dbtype = string.lower(dbtype)
        if dbtype[:4] == 'int(' or dbtype == 'integer':
            return 1
    
    def sqlStringAndValue(self, val, attr, dbtype):
        newval = self.typeCheckAndConvert(val, attr, dbtype)
        if _isString(dbtype):
            newval = "'" + MySQL.escape(str(newval)) + "'"
        return str(newval), None


    def getBindVariable(self):
        raise NotImplemented, 'No bind variables for mysql driver'
    
    def getAutoIncrement(self, name):
        return int(self.conn.do("SELECT LAST_INSERT_ID()")[0][0])

    def execute(self, sql, values, attributes):
        if self.verbose:
            print 'SQL>', sql
        cur = self.conn.query(sql)
        try:
            result = cur.fetchrows()
        except MySQL.error:
            return cur.affectedrows()

        if attributes is None:
            return result, cur.fields()
        fields = cur.fields()
        fields = map(lambda x:string.upper(x[0]), fields)
        return self.convertResultRows(fields, attributes, result)

    def convertResultRows(self, colnames, attributes, rows):
        newresult = []
        for row in rows:
            d = {}
            for item, desc in map(None, row, colnames):
                #do dbtype->python type conversions here
                a = attributes[desc]
                if _isDateKind(a):
                    d[desc] = _dateConvertFromDB(item)
                else:
                    d[desc] = item
            newresult.append(d)

        return newresult

    def typeCheckAndConvert(self, val, aname, attr):
        if _isDateKind(attr):
            if not Date.isDateTime(val) and not val == PyDBI.SYSDATE:
                raise TypeError,'trying to assign %s to %s and is not a date'%(
                    val, aname)
            val = _dateConvertToDB(val)
        elif (_isNumber(attr) and
              not isinstance(val, types.FloatType) and
              not isinstance(val, types.IntType)):
                raise TypeError, ('trying to assign %s to %s and is not'
                                  ' a number') % (val, aname)
        elif _isString(attr) and not isinstance(val, types.StringType):
            raise TypeError, 'trying to assign %s to %s and is not a string'% (
                val, aname)
        
        return val

    #methods not needed for mysql
    def resetQuery(self): pass
    def getSequence(self, name): pass
    def postInsertUpdate(self, object, newvals, isinsert): pass
    def commit(self): pass
    def rollback(self): pass
    

def _isNumber(attr):
    attr = string.upper(attr)
    for i in ('TINYINT', 'SMALLINT', 'MEDIUMINT', 'INT', 'INTEGER',
              'BIGINT', 'REAL', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC'):
        if attr[:len(i)] == i:
            return 1

def _isString(attr):
    attr = string.upper(attr)

    for i in ('VARCHAR', 'CHAR'):
        if attr[:len(i)] == i:
            return 1
    return attr in ('TINYBLOB', 'BLOB', 'MEDIUMBLOB', 'LONGBLOB',
                    'TINYTEXT', 'TEXT', 'MEDUIMTEXT', 'LONGTEXT')
        
def _isDateKind(type):
    type = string.upper(type)
    if type in ('TIME', 'TIMESTAMP', 'DATETIME', 'DATE'):
        return 1

def _dateConvertFromDB(item):
    if item is None:
        return item
    if string.find(item, '-') == -1: #timestamp form
        y = item[:4]
        mo = item[4:6]
        d = item[6:8]
        h = item[8:10]
        mi = item[10:12]
        s = item[12:14]
    else:
        y=item[:4]
        mo = item[5:7]
        d = item[8:10]
        h = item[11:13]
        mi = item[14:16]
        s = item[17:19]
    return DateTime.DateTime(int(y), int(mo), int(d), int(h), int(mi),
                             int(s))

def _dateConvertToDB(dt):
    if dt == PyDBI.SYSDATE:
        dt = DateTime.now()
    return '%04d%02d%02d%02d%02d%02d' % (dt.year, dt.month, dt.day,
                                         dt.hour, dt.minute, dt.second)
