from itertools import izip

from PyDO.log import *
from PyDO.operators import BindingConverter

class DBIBase(object):
    """base class for db connection wrappers"""
    paramstyle='format'
    autocommit=False
    
    def __init__(self, connectArgs, verbose=False):
        self.conn=self._connect(connectArgs)
        self.verbose=verbose

    def commit(self):
        """commits a transaction"""
        self.conn.commit()

    def rollback(self):
        """rolls back a transaction"""
        self.conn.rollback()

    def cursor(self):
        return self.conn.cursor()

    def _connect(self):
        raise NotImplementedError

    def getConverter(self):
        """returns a converter instance."""
        return BindingConverter(self.paramstyle)

    def execute(self, sql, values=(), fields=()):
        """Executes the statement with the values and does conversion
        of the return result as necessary.
        result is list of dictionaries, or number of rows affected"""
        if self.verbose:
            debug("SQL: %s", (sql,)
            debug("bind variables: %s", (values,))

        c=self.conn.cursor()
        if values:
            c.execute(sql, values)
        else:
            # I don't want to assume that all drivers will like None,
            # or (), or {}, equally when there are no bind variables
            c.execute(sql)
        resultset=cur.fetchall()
        if not resultset:
            return cur.rowcount
        res=self._convertResultSet(cur.description, resultset)
        c.close()
        return res

    def _convertResultSet(description, resultset):
        """internal function that turns a result set into a list of dictionaries."""
        fldnames=[x[0] for x in description]
        return [dict(izip(fldnames, row)) for row in resultset]
    _convertResultSet=staticmethod(_convertResultSet)

       
    def getSequence(self, name):
        """If db has sequences, this should return the sequence named name"""
        pass

    def getAutoIncrement(self, name):
        """if things like mysql where can get the sequence after the insert"""
        pass

