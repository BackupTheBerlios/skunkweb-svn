import re

from pydo.dbi import DBIBase
from pydo.field import Field
from pydo.exceptions import PyDOError

import sqlite

_createPat=re.compile(r'\((.*)\)', re.DOTALL)
_incrPat=re.compile('INT(:?EGER)?\s+PRIMARY\s+KEY', re.IGNORECASE)

class SqliteDBI(DBIBase):
    # sqlite uses an auto increment approach to sequences
    auto_increment=True

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
        fields, unique, auto_increment=self._parse_create_sql(createSql)
        return fields, unique, auto_increment

##     def _parse_create_sql(sql):
##         m=_createPat.search(sql)
##         if m:
##             clauses=[x.strip() for x in m.group(1).split(',')]
##             auto_increment=[]
##             unique=[]
##             flds=[]
##             for clause in clauses:
##                 clause=clause.lower()
##                 if clause.startswith('unique'):
##                     # separate unique constraint
##                     unique.append(self._parse_unique(clause))
##                         continue
##                     elif name =='check':
##                         # ignore
##                         continue
##                     elif name=='primary' and rest.startswith('key'):
                        
##                     elif _incrPat.search(rest):
##                         auto_increment.append(name)
##                         unique.append(name)
##                     elif _uniquePat.search(rest):
##                         unique.append(name)
##                     if rest.lower() in ('int', 'integer') \
##                            and 'primary key' in rest.lower():
##                         auto_increment=(name,)

##                         break
##             else:
##                 auto_increment=()
##             return [Field(*x) for x in fields], auto_increment
##         else:
##             raise PyDOError, "could not parse create table sql: %s" % sql
##     _parse_create_sql=staticmethod(_parse_create_sql)



## startpat=re.compile(r'\s*CREATE\s+TABLE\s+\w+\(', re.DOTALL | re.IGNORECASE)
## uniquepat=re.compile(r'\s+UNIQUE\s+\(', re.DOTALL | re.IGNORECASE)
## pkpat=re.compile(r'\s+PRIMARY\s+KEY\s+(', re.DOTALL | re.IGNORECASE)
## checkpat=re.compile(r'\sCHECK\s+\(', re.DOTALL | re.IGNORECASE)
## fldpat=re.compile(r'\s+(\w+).*?(CHECK\s+\(|,)', re.DOTALL | re.IGNORECASE)
## flduniquepat=re.compile(r'UNIQUE', re.IGNORECASE)
## fldautoincpat=re.compile(r'INTEGER\s+PRIMARY\s+KEY', re.IGNORECASE)

## def _parse_create(sql):
##     """
##     parses a create table statement, pulling out only the information
##     I care about

##     CREATE TABLE whatever (
##        field1 integer primary key,
##        field2 whatevertype not null,
##        field3 text unique not null,
##        field4 text not null check (blah),
##        field5 text not null,
##        check (x is not y),
##        unique (field4, field5),
##        primary key (field4, field5)
##     );

##     state changes:

##       * at ( after create table, before fields: state is FIELDS
##       * at unique (; state is UNIQUE
##       * at primary key (; state is PK
##       * at ); finish.
##     """
##     # accumulate data here
##     flds=[]
##     unique=[]
##     seq=[]
##     # parser state
##     offset=0
##     state='begin'
##     lenstr=len(sql)
##     # move up to the start of the fields
##     m=startpat.match(sql)
##     if not m:
##         raise ValueError, "sql not a create table statement"
##     offset=m.end()
##     while offset < lenstr:
##         if state=='begin':
##             # expect either a field,
##             # a check, a unique, a pk,
##             # or finish
##             m=checkpat.match(sql, offset)
##             if m:
##                 offset=m.end()
##                 state='check'
##                 continue
##             m=uniquepat.match(sql, offset)
##             if m:
##                 offset=m.end()
##                 state='unique'
##                 continue
##             m=pkpat.match(sql, offset)
##             if m:
##                 offset=m.end()
##                 state='unique'
##                 continue
##             m=endpat.match(sql, offset)
##             if m:
##                 break
##             # must be a field
##             m=fieldpat.match(sql, offset)
##             if m:
##                 fld=m.group(1)
##                 flds.append(fld)
##                 e1, e2=m.end(1), m.start(2)
##                 if flduniquepat.search(sql, e1, e2)):
##                     unique.append(fld)
##                 if fldautoincpat.search(sql, e1, e2):
##                     seq.append(fld)
##                 offset=m.end()                    
##                 if m.group(2)!==',':
##                     state='check'
##                 continue
##         elif state=='check':
##             # to do

##         elif state=='unique':
##             # to do
        
    
    

