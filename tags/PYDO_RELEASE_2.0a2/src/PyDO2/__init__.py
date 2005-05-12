"""PyDO (Python Data Objects) is an object-relational wrapper for
relational databases.  It provides a convenient API for retrieving and
manipulating data without constraining in any way how the data is
persisted at the RDBMS level.  Supported databases are:

   * postgresql
   * mysql
   * sqlite

"""

from PyDO2.exceptions import *
from PyDO2.field import *
from PyDO2.base import *
from PyDO2.operators import *
from PyDO2.dbi import *
from PyDO2.dbtypes import *
from PyDO2.log import *
from PyDO2.joins import *

__version__='2.0a2'
