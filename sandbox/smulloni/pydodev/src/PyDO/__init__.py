"""PyDO (Python Data Objects) is an object-relational wrapper for
relational databases.  It provides a convenient API for retrieving and
manipulating data without constraining in any way how the data is
persisted at the RDBMS level.  Supported databases are:

   * postgresql
   * mysql
   * sqlite

Others that may be supported:

   * gadfly
   * firebird 
   * maxdb (==sapdb)
   * oracle

Possibly down the line:   
   * sybase
   * SQL Server
"""

from PyDO.exceptions import *
from PyDO.field import *
from PyDO.pydo import *
from PyDO.operators import *
