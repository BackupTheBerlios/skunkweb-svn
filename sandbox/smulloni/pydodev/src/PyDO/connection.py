try:
    import mx.DateTime as M
    haveMx=True
except ImportError:
    haveMx=False

import datetime

class DBIBase(object):
    """base class for db connection wrappers"""
    bindVariables=False

    def __init__(self, connectArgs):
        self.conn=self._connect(connectArgs)

    def _connect(self):
        raise NotImplementedError

    def autocommit():
        def fget(self):
            return self._autocommit
        def fset(self, val):
            b=bool(val)
            self.conn.autocommit(b)
            self._autocommit=b
        return (fget, fset, None, None)
    autocommit=property(autocommit())
    
    def sqlStringAndValue(self, val, field):
        """Returns a sql string and a value.  The literal is to be put into
	the sql query, the value should is put into the value list that is
	subsequently passed to execute().

        The reason for this is for example, using bind variables in the
        generated sql, you want to return a bind variable string and the
        value to be passed.  If doing such things requires state, you can
        clear it in resetQuery().

        """

    def execute(self, sql, fields, values=None):
        """Executes the statement with the values and does conversion
        of the return result as necessary.
        result is list of dictionaries, or number of rows affected"""
        if self.verbose:
            self.log(sql)
        c=self.conn.cursor()
        if values:
            c.execute(sql, values)
        else:
            c.execute(sql)
        result=cur.fetchall()
        if not result:
            return cur.rowcount
        fldnames=[x[0] for x in cur.description]
        


    def convertResultRows(self, fields, rows):
        """converts the result list into a list of dictionaries keyed
        by column name, and data type conversion specified by the
        attributeKinds dictionary (keyed by attribute, valued by database
        datatype).
        """
        
    def resetQuery(self):
        """Reset things like bind variable numbers if necessary before a query
        Need only if there is state between sqlLiterals because of bind
        variables, otherwise, don't need this.  Called before a query is
        executed.
        """

    def getSequence(self, name):
        """If db has sequences, this should return the sequence named name"""


    def getAutoIncrement(self, name):
        """if things like mysql where can get the sequence after the insert"""


    def typeCheckAndConvert(self, value, field):
        """check values type to see that it is valid and subsequently
        do any conversion to value necessary to talk to the database with
        it, i.e. mxDateTime to database date representation"""
        
    def postInsertUpdate(self, PyDOObject, adict, isInsert):
        """to do anything needed after an insert or update of the values
        into table.  Specifically to handle cases like blobs where you
        insert/update with a new blob, but have to select for update and
        then deal with the blob post factum

        PyDOObject is the object being affected
        adict is the dict of new values
        isInsert is a boolean stating whether or not this is an insert (true)
                 or an update (false).
        """

strftimeTypes=[datetime.datetime]
if haveMx:
    strftimeTypes.append(M.DateTimeType)

class ConverterBase(object):
    def __init__(self):
        self.values=[]
        
    def __call__(self, val):
        if isinstance(val, strftimeTypes):
            return repr(val.strftime(DT_FORMAT))
    
