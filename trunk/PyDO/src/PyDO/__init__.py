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

from pydo.exceptions import *
from pydo.field import *
from pydo.base import *
from pydo.operators import *
from pydo.dbi import *
from pydo.log import *

__version__='2.0a0'
