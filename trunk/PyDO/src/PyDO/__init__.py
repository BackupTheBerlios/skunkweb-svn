"""PyDO (Python Data Objects) is an object-relational wrapper for
relational databases.  It provides a convenient API for retrieving and
manipulating data without constraining in any way how the data is
persisted at the RDBMS level.  Supported databases are:

   * postgresql
   * mysql
   * sqlite

"""

from PyDO.exceptions import *
from PyDO.field import *
from PyDO.base import *
from PyDO.operators import *
from PyDO.dbi import *
from PyDO.dbtypes import *
from PyDO.log import *
from PyDO.joins import *

__version__='2.0a0'
