try:
    set
except NameError:
    from sets import Set as set
    
from PyDO.field import Field
from PyDO.exceptions import PyDOError
from PyDO.operators import *

class _metapydo(type):
    """metaclass for _pydobase.
    Manages attribute inheritance.
    """
    
    def __init__(cls, cl_name, bases, namespace):
        # handle inheritance of (private) class attributes
        revbases=[x for x in bases[::-1] if x not in (object, dict)]
        for a, t in (('_fields', dict),
                     ('_unique', set),
                     ('_sequenced', dict),
                     ('_auto_increment', dict)):
            setattr(cls, a, t())
            for b in revbases:
                o=getattr(b, a, None)
                if o:
                    # set & dict both have update()
                    getattr(cls, a).update(o)
                    
        # add attributes declared for this class
        for f in cls.fields:
            # support for tuple syntax for plain Jane fields
            if not isinstance(f, Field):
                f=Field(*f)
            # add to field container
            cls._fields[f.name]=f

        # manage this class's declared attributes
        cls._unique.update(cls.unique)
        cls._sequenced.update(cls.sequenced)
        cls._auto_increment.update(cls.auto_increment)
        
        # add attribute access to fields
        if cls.use_attributes:
            for name in cls._fields:
                if not hasattr(cls, name):
                    # a field is also a descriptor
                    setattr(cls, name, self._fields[name])


class PyDO(dict):
    """ Base class for PyDO data classes."""

    __metaclass__=_metapydo

    table=None
    mutable=1
    use_attributes=1
    connectionAlias=None
    
    fields=()
    unique=[]
    sequenced={}
    auto_increment={}

    def update(self, adict):
        """ Part of dictionary interface for field access"""
        # call (normally empty) hook for modifying the update
        d=self.onUpdate(adict)
        # Check that the fields in the dictionary are kosher
        self._validateFields(d)
        # do the actual update
        self.updateRawValues(self, d)
        # if successful, modify the object's field data
        super(PyDO, self).update(self, d)

    def onUpdate(self, adict):
        """a hook for subclasses to modify updates; 
        by default returns the original data unchanged."""
        return adict

    def dict(self):
        return dict(self)

    def copy(self):
        return self.__class__(dict(self).copy())

    def getColumns(cls, qualified=False):
        """Returns a list of all columns in this table, in no particular order.

        If qualified is true, returns fully qualified column names
        (i.e., table.column)
        """
        if not qualified:
            return cls._fields.keys()
        else:
            t=cls.table
            return ["%s.%s" % (t, x) for x in cls._fields.iterkeys()]
    getColumns=classmethod(getColumns)

    def _validateFields(cls, adict):
        """a simple field validator that verifies that the keys
        in the dictionary passed are declared fields in the class.
        """
        for k in adict:
            if not cls._fields.has_key(k):
                raise KeyError, "object %s has no field %s" %\
                      (cls, k)
    _validateFields=classmethod(_validateFields)

    # DB interface

    def getDBI(cls):
        """return the database interface"""
        conn=DBIGetConnection(cls.connectionAlias)
        conn.resetQuery()
        return conn
    getDBI=classmethod(getDBI)


    def commit(cls):
        """ Commit changes to database"""
        cls.getDBI().commit()
    commit=classmethod(commit)


    def rollback(cls):
        """ Rollback current transaction"""
        cls.getDBI().rollback()
    rollback=classmethod(rollback)


    def new(cls, refetch=None,  **fieldData):
        """create and return a new data class instance using the values in
        fieldData.  This will also effect an INSERT into the database.  If refetch
        is true, effectively do a getUnique on cls.
        """
        if not cls.mutable:
            raise ValueError, 'cannot make a new immutable object!'

        # sanity check the field data
        cls._validateFields(fieldData)
        
        conn = cls.getDBI()
        for s, sn in cls.sequenced.items():
            if not fieldData.has_key(s):
                fieldData[s] = conn.getSequence(sn)
        
        cols = []
        values = []
        vals = []
        for dbname, v in fieldData.iteritems():
            cols.append(dbname)
            lit, val = conn.sqlStringAndValue(v, cls._fields[dbname])
            values.append(lit)
            vals.append(val)
        sql = 'INSERT INTO %s (%s) VALUES  (%s)' \
              % (cls.table,
                 ', '.join(cols),
                 ', '.join(values))
        res = conn.execute(sql, vals, flds)
        if res != 1:
            raise PyDOError, "inserted %s rows instead of 1" % res
        
        if cls.auto_increment:
            for k, v in cls.auto_increment.items():
                if not fieldData.has_key(k):
                    fieldData[k] = conn.getAutoIncrement(v)
        
        conn.postInsertUpdate(cls, fieldData, 1)
        if not refetch:
            return cls(fieldData)
        return cls.getUnique(**fieldData)
    
    new=classmethod(new)
    
    def getUnique(cls, **fieldData):
        """ Retrieve one particular instance of this class.
        
        Given the attribute/value pairs in fieldData, retrieve a unique row
        and return a data class instance representing said row or None
        if no row was retrieved.
        """
                         
        cls._validateFields(fieldData)
        unique = cls._matchUnique(fieldData)
        conn = cls.getDBI()
        where, values = cls._uniqueWhere(conn, fieldData)
        sql = "%s WHERE %s" % (cls._baseSelect(), where)
        results = conn.execute(sql, values, cls._fields)
        if not results:
            return
        if len(results) > 1:
            raise PyDOError, 'got more than one row on unique query!'
        if results:
            return cls(results[0]) 
       getUnique=classmethod(getUnique)    
            
    def _orderByString(order_by):
        
        order_list = []
        
        for item in order_by:
            if type(item) == types.StringType:
                order_list.append(item)
            else:
                order_list.append(' '.join(item))
                    
        sql = ' ORDER BY %s' % ', '.join(order_list)
        
        return sql
    _orderByString=staticmethod(_orderByString)


    def _baseSelect(cls, qualified=False):
        """returns the beginning of a select statement for this object's table."""
        return 'SELECT %s FROM %s' % (', '.join(cls.getColumns(qualified)),
                                      cls.table)
    _baseSelect=classmethod(_baseSelect)
    
##     def _prepareSelect(cls, **fieldData):
##         """ Prepare the SQL required to retrieve some objects by keyword.
        
##         Given the attribute/value pairs in fieldData, return sql statement,
##         values to be used in a call to conn.execute.
##         """
##         sql = [cls._baseSelect()]
##         where = []
##         values = []
##         order = []
##         limit = 0
##         offset = 0
##         conn = cls.getDBI()
##         for k, v in fieldData.items():
##             if k == 'order':
##                 if type(v) == types.StringType:
##                     order.append(v)
##                 else:
##                     order.extend(v)
##                 continue
##             elif k == 'limit':
##                 limit = v
##                 continue
##             elif k == 'offset':
##                 offset = v
##                 continue
##             else:
##                 lit, val = conn.sqlStringAndValue(v, cls._fields[k])
##                 where.append("%s=%s" % (k, lit))
##                 values.append(val)
        
##         if where:
##             sql.extend([' WHERE ', 'AND '.join(where)])
                
##         if order:
##             sql.append(cls._orderByString(order))
        
##         if limit:
##             sql.append(' LIMIT %d' % limit)
            
##         if offset:
##             sql.append(' OFFSET %d' % offset)
            
##         return ''.join(sql), values
##     _prepareSelect=classmethod(_prepareSelect)
    
##     def getSome(cls, **fieldData):
##         """ Retrieve some objects by keyword
        
##         Given the attribute/value pairs in fieldData, return a (potentially
##         empty) list of data class instances representing the rows that
##         fulfill the constraints in fieldData.
##         """
##         cls._validateFields(fieldData)                           
##         sql, values=cls._prepareSelect(**fieldData)
##         conn=cls.getDBI()
##         results = conn.execute(sql, values, cls._fields)
##         if type(results)==types.ListType:
##             return map(cls, results)
##         else:
##             return []
##     getSome=classmethod(getSome)
    
    def class_getSome(cls,
                      order=None,
                      limit=None,
                      offset=None,
                      *args,
                      **fieldData):
        """ Retrieve some objects of this particular class.
        
        Allows you to use the operator objects in PyDO.operators to be
        able to use sql operators other than the implicit AND as
        used by the other static get methods.
        
        The **fieldData argument is the same as the other static get methods.
        The *args argument however allows you to combine operators to
        do operations like OR, NOT, LIKE, etc. For example, the following
        would get all rows where the last name field was LIKE Ingers%.
        
        obj.getSomeWhere(LIKE(FIELD('last_name'), ('Ingers%')))
        
        """
        if len(args)==1 and isinstance(args[0], str):
            if fieldData:
                raise ValueError, "cannot pass keyword args when including sql string"
            sql=args[0]
        else:
            cls._validateFields(fieldData)
            andValues=list(args)
            for k, v in fieldData.items():
                if k not in ('order', 'offset', 'limit'):
                    andValues.append(operators.EQ(operators.FIELD(k), v))
            andlen=len(andValues)
            if andlen > 1:
                sql=repr(AND(*andValues))
            elif andlen==1:
                sql=repr(andValues[0])
            else:
                sql=''
        
            if order:
                if isinstance(order, str):
                    order=[order]

        query=[cls._baseSelect()]
        if sql:
            query.extend(['WHERE', sql])
        if order:
            query.append(cls._orderByString(order))
        # this will have to delegate to the driver,
        # to deal with mysql....
        if limit:
            query.append('LIMIT %d' % limit)
        if offset:
            query.append('OFFSET %d' % offset)
        query=' '.join(query)
        conn = cls.getDBI()
        ## XXXX
        # what about values?  What am I giving up re Oracle?
        results = conn.execute(query, (), cls._fields)
        if results and isinstance(results, list):
            return map(cls, results)
        else:
            return []


    def scatterFetchSQL(cls, objs):
        """ Select objects from multiple tables
        
        Do a scatter fetch (a select from more than one table) based
        on the relation information in objs which is of the form:
        [
        (object, attributes, destinationObject, destinationAttributes),
        (object, attributes, destinationObject, destinationAttributes)
        ]
        This basically states that objects attributes are a foreign key to
        destinationObject's destinationAttributes.
        
        For example, if you have User and UserResidence classes, a scatter
        fetch may be simply:
        userObj.scatterFetchSQL( [ (UserResidence, 'USER_OID', User, 'OID') ] )
        which if executed would return a list of tuples of:
        (userObj, userResObj)
        where userObj.['OID'] == userResObj['USER_OID']
        
        This function returns sql, baseColumnNames, and a modified version of
        the objs argument.
        """
        objs = ((cls, None, None, None),) + tuple(objs)
        cols = []
        for obj in objs:
            cols.extend(obj[0].getColumns(1))
        tabs = map(lambda x:x[0].table, objs)
        sql = "SELECT %s FROM %s WHERE " % (', '.join(cols),
                                            ', '.join(tabs))
        j = []
        for obj, attr, dobj, dattr in objs:
            if type(attr) in (types.TupleType, types.ListType):
                if type(dattr) != type(attr):
                    raise TypeError, ("source and destination attributes for"
                    " %s/%s aren't of same length") % (
                    obj, dobj)
                
                for attri, dattri in map(None, attr, dattr):
                    j.append('%s.%s = %s.%s' % (obj.table, cls._field_dict[attri]['dbName'],
                    dobj.table, cls._field_dict[dattri]['dbName']))
                
            else:
                if dobj:
                    j.append('%s.%s = %s.%s' % (obj.table, cls._field_dict[attr]['dbName'],
                    dobj.table, cls._field_dict[dattr]['dbName']))
        sql = sql + ' AND '.join(j)
        return sql, cols, objs
    scatterFetchSQL=classmethod(scatterFetchSQL)


    def scatterFetchPost(cls, objs, sql, vals, cols):
        """handle the execution and processing of a scatter fetch to produce
        a result list -- returns the list of tuples referred to in the
        docstring of scatterFetchSQL"""
        conn = cls.getDBI()
        results, fields = conn.execute(sql, vals, None)
        if not results:
            return []
        endResults = []
        
        sliceSets = []
        counter = 0 
        for obj in objs:
            cols = obj[0].getColumns()
            lenCols = len(cols)
            sliceSets.append([counter, counter+lenCols, obj[0]])
            counter = counter+lenCols
        
        resultSets = {}
        
        for result in results:
            counter = 0
            for set in sliceSets:
                if not resultSets.has_key(counter):
                    resultSets[counter] = []
                resultSets[counter].append(result[set[0]: set[1]])
                counter = counter + 1
        
        cvtedResultSets = {}
        for i in range(len(objs)):
            obj = objs[i][0]
            r = map(obj, conn.convertResultRows(obj.getColumns(),
                                                obj._fields,
                                                resultSets[i]))
            cvtedResultSets[i] = r
        
        result = []
        for i in range(len(cvtedResultSets[0])):
            l = []
            for j in range(len(cvtedResultSets)):
                l.append(cvtedResultSets[j][i])
            result.append(l)
        return result
    scatterFetchPost=classmethod(scatterFetchPost)
    
    def scatterFetch(cls, objs, **kw):
        """see scatterFetchSQL for format of objs and getSome for format
        of **kw
        """
        
        sql, cols, objs = cls.scatterFetchSQL(objs)
        
        conn = cls.getDBI()
        where = []
        values = []
        for k, v in kw.items():
            notFlag = ''
            if isinstance(v, NOT):
                notFlag = '!'
                v = v.val
            lit, val = conn.sqlStringAndValue(v, cls._fields[k])
            
            where.append("%s.%s %s= %s" % (cls.table, k, notFlag, lit))
            values.append(val)
        whereClause = ' AND '.join(where)
        if whereClause:
            sql = sql + " AND " + whereClause
        
        #make where clause here from **kw
        return cls.scatterFetchPost(objs, sql, values, cols)
    scatterFetch=classmethod(scatterFetch)
    
    ##############################
    ## Public instance methods
    ##############################
    
    def updateRawValues(self, dict):
        """update self in database with the values in dict"""
        if not self.mutable:
            raise ValueError, "instance isn't mutable!"
        sql = "UPDATE %s SET " % self.table
        sets = []
        values = []
        conn = self.getDBI()
        atts = []
        
        for dbname, value in dict.items():
            fld=self._fields[dbname]
            conn.typeCheckAndConvert(v, fld)
            lit, val = conn.sqlStringAndValue(v, fld)
            atts.append(dbtype)
            values.append(val)
            sets.append("%s = %s" % (dbname, lit))
        
        where, wvalues = self._uniqueWhere(conn, self._dict)
        values = values + wvalues
        sql = '%s%s WHERE %s' % (sql, ', '.join(sets), where)
        result = conn.execute(sql, values, self.dbColumns)
        if result > 1:
            raise PyDOError, "updated %s rows instead of 1" % result        
        conn.resetQuery()
        conn.postInsertUpdate(self, dict, 0)
    
    def delete(self):
        """remove the row that represents me in the database"""
        if not self.mutable:
            raise ValueError, "instance isn't mutable!"
        conn = self.getDBI()
        unique, values = self._uniqueWhere(conn, self._dict)
        sql = 'DELETE FROM %s WHERE %s' % (self.table, unique)
        conn.execute(sql, values, self.dbColumns)
        # shadow the class attribute with an instance attribute
        self.mutable = 0
    
    def refresh(self):
        """refetch myself from the database"""
        obj = apply(self.getUnique, (), self._dict)
        if not obj:
            raise ValueError, "current object doesn't exist in database!"
        #        mutable = self.mutable #save if was deleted, it still is deleted
        self._dict = obj._dict
    #        self.mutable = self._cls.mutable
    
    def joinTableSQL(self,
                     thisAttrNames,
                     pivotTable,
                     thisSideColumns,
                     thatSideColumns,
                     thatObject,
                     thatAttrNames,
                     extraTables = []):
        """Handle many to many relations.  In short, do a
        
        SELECT thatObject.getColumns(1)
        FROM thatObject.table, pivotTable
        WHERE pivotTable.thisSideColumn = self[myAttrName]
        AND pivotTable.thatSideColumn = thatObject.table.thatAttrName
        
        and return a list of thatObjects representing the resulting rows.
        """
        
        thisAttrNames = self._convertTupleKW(_tupleize(thisAttrNames))
        thisSideColumns = _tupleize(thisSideColumns)
        thatSideColumns = _tupleize(thatSideColumns)
        thatAttrNames = self._convertTupleKW(_tupleize(thatAttrNames))
        
        if len(thisSideColumns) != len(thisAttrNames):
            raise ValueError, ('thisSideColumns and thisAttrNames must '
            'contain the same number of elements')
        if len(thatSideColumns) != len(thatAttrNames):
            raise ValueError, ('thatSideColumns and thatAttrNames must '
            'contain the same number of elements')
        
        conn = self.getDBI()
        
        sql = '%s,%s WHERE ' % (thatObject._baseSelect(1),
                                ', '.join([pivotTable]+extraTables))
        
        thisJoin = []
        vals = []
        
        for attr, col in map(None, thisAttrNames, thisSideColumns):
            lit, val = conn.sqlStringAndValue(
                self[attr], attr, self.dbColumns[attr])
            thisJoin.append('%s.%s = %s' % (pivotTable, col, lit))
            vals.append(val)
        
        sql = '%s%s AND ' % (sql, ' AND '.join(thisJoin))
        
        thatJoin = []
        thatTable = thatObject.table
        for attr, col in map(None, thatAttrNames, thatSideColumns):
            thatJoin.append('%s.%s = %s.%s' % (pivotTable,
                                               col,
                                               thatTable,
                                               attr))
        
        sql = '%s%s' % (sql, ' AND '.join(thatJoin))
        return sql, vals
    
    
    def joinTable(self,
                  thisAttrNames,
                  pivotTable,
                  thisSideColumns,
                  thatSideColumns,
                  thatObject,
                  thatAttrNames):
        """see joinTableSQL for arguments
        
        This method executes the statement returned by joinTableSQL
        with the arguments and produces object from them.
        """
        
        conn = self.getDBI()
        sql, vals = self.joinTableSQL(thisAttrNames, pivotTable,
        thisSideColumns, thatSideColumns,
        thatObject, thatAttrNames)
        results = conn.execute(sql, vals, thatObject.dbColumns)
        return map(thatObject, results)        
    
    

    def _matchUnique(cls, kw):
        """return a tuple of column names that will uniquely identify
        a row given the choices from kw
        """
        for unique in cls._unique:
            if isinstance(unique, str):
                if kw.has_key(unique) and kw[unique] is not None:
                    return (unique,)
            elif isinstance(unique, tuple):
                for u in unique:
                    if not kw.has_key(u):
                        break
                else:
                    return unique
    _matchUnique=classmethod(_matchUnique)

    def _uniqueWhere(cls, conn, kw):
        """given a connection and kw, using _matchUnique, generate a
        where clause to select a unique row.
        """
        unique = cls._matchUnique(kw)
        if not unique:
            raise ValueError, 'No way to get unique row! %s %s' % (
            str(kw), unique)
        
        where = []
        values = []
        for u in unique:
            lit, val = conn.sqlStringAndValue(kw[u], u, cls.dbColumns[u])
            where.append("%s = %s" % (u, lit))
            values.append(val)
        return ' AND '.join(where), values
    _uniqueWhere=classmethod(_uniqueWhere)


def _tupleize(item):
    if type(item) == types.TupleType:
        return item
    return (item,)


    
__all__=['PyDO']
