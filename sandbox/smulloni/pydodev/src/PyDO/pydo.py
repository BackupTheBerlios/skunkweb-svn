try:
    set
except NameError:
    from sets import Set as set

from PyDO.dbi import getConnection
from PyDO.field import Field
from PyDO.exceptions import PyDOError
from PyDO.operators import *
from PyDO.log import debug

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
            if isinstance(f, str):
                f=Field(f)
            elif not isinstance(f, Field):
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
                    setattr(cls, name, cls._fields[name])


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
        self._update_raw(d)
        # if successful, modify the object's field data
        super(PyDO, self).update(d)

    def onUpdate(self, adict):
        """a hook for subclasses to modify updates; 
        by default returns the original data unchanged."""
        return adict

    def __setitem__(self, k, v):
        self.update({k:v})

    def _update_raw(self, adict):
        """update self in database with the values in adict"""

        # precondition: fields in adict are already validated
        
        if not self.mutable:
            raise ValueError, "instance isn't mutable!"

        conn=self.getDBI()
        converter=conn.getConverter()
        sqlbuff=["%s  = %s" % (x, converter(y)) for x, y in adict.iteritems()]
        values=converter.values
        where, wvals=self._uniqueWhere(conn, self)
        values+=wvals
        sql = "UPDATE %s SET %s WHERE %s" % (self.table,
                                             ", ".join(sqlbuff),
                                             where)
        result=conn.execute(sql, values, self._fields)
        if result > 1:
            raise PyDOError, "updated %s rows instead of 1" % result        

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
        conn=getConnection(cls.connectionAlias)
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
        cols=fieldData.keys()
        vals=[fieldData[c] for c in cols]
        converter=conn.getConverter()
        converted=map(converter, vals)
        
        sql = 'INSERT INTO %s (%s) VALUES  (%s)' \
              % (cls.table,
                 ', '.join(cols),
                 ', '.join(converted))
        res = conn.execute(sql, converter.values, cls._fields)
        if res != 1:
            raise PyDOError, "inserted %s rows instead of 1" % res
        
        if cls.auto_increment:
            for k, v in cls.auto_increment.items():
                if not fieldData.has_key(k):
                    fieldData[k] = conn.getAutoIncrement(v)
        
        if not refetch:
            return cls(fieldData)
        return cls.getUnique(**fieldData)
    new=classmethod(new)


    def _matchUnique(cls, kw):
        """return a tuple of column names that will uniquely identify
        a row given the choices from kw
        """
        for unique in cls._unique:
            if isinstance(unique, (unicode,str)):
                if kw.get(unique)!=None:
                    return (unique,)
            elif isinstance(unique, (list,tuple)):
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
        debug(unique)
        if not unique:
            raise ValueError, 'No way to get unique row! %s %s' % \
                  (str(kw), unique)
        converter=conn.getConverter()        
        if len(unique)==1:
            sql=str(EQ(FIELD(unique[0]), kw[unique[0]], converter=converter))
        else:
            sql=str(AND(converter=converter, *[EQ(FIELD(u), kw[u]) for u in unique]))
        return sql, converter.values
    _uniqueWhere=classmethod(_uniqueWhere)
    
    
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
            
    def _baseSelect(cls, qualified=False):
        """returns the beginning of a select statement for this object's table."""
        return 'SELECT %s FROM %s' % (', '.join(cls.getColumns(qualified)),
                                      cls.table)
    _baseSelect=classmethod(_baseSelect)
    
    def getSome(cls,
                *args,
                **fieldData):
        """ Retrieve some objects of this particular class.

        [todo: examples of use of operators, column-name keyword args,
        order, limit, and offset.]

        If you use SQL directly and pass variables, it is up to
        you to use the same paramstyle as the underlying driver.
        
        """
        order=fieldData.pop('order', None)
        limit=fieldData.pop('limit', None)
        offset=fieldData.pop('offset', None)
        
        conn=cls.getDBI()

        if args and isinstance(args[0], str):
            if fieldData:
                raise ValueError, "cannot pass keyword args when including sql string"
            sql=args[0]
            values=args[1:]

            if len(values)==1 and isinstance(values[0], dict):
                values=values[0]
        else:
            cls._validateFields(fieldData)
            andValues=list(args)
            converter=conn.getConverter()
            for k, v in fieldData.items():
                    andValues.append(EQ(FIELD(k), v, converter=converter))
            andlen=len(andValues)
            converter.reset()            
            if andlen > 1:
                sql=repr(AND(converter=converter, *andValues))
            elif andlen==1:
                sql=repr(andValues[0])
            else:
                sql=''
            values=converter.values
            
        query=[cls._baseSelect()]
        if sql:
            query.extend(['WHERE', sql])
        if filter(None, (order, limit, offset)):
            query.append(conn.orderByString(order, limit, offset))
        query=' '.join(query)

        results = conn.execute(query, values, cls._fields)
        if results and isinstance(results, list):
            return map(cls, results)
        else:
            return []
    getSome=classmethod(getSome)

    def clear(self):
        raise AttributeError, "PyDO classes don't implement clear()"

    def delete(self):
        """remove the row that represents me in the database"""
        if not self.mutable:
            # this used to be a value error, but there are no parameters,
            # so I'm using PyDOError
            raise PyDOError, "instance isn't mutable!"
        if not self.unique:
            raise PyDOError, "cannot delete, no unique index!"
        conn = self.getDBI()
        unique, values = self._uniqueWhere(conn, self)
        # if the class has unique constraints, and all data
        # is presented, there will be something returned from
        # unique unless someone is doing bad things to the
        # object 
        assert unique
        sql = 'DELETE FROM %s WHERE %s' % (self.table, unique)
        conn.execute(sql, values, self._fields)
        # shadow the class attribute with an instance attribute
        self.mutable = False

    
    def refresh(self):
        """refetch myself from the database"""
        obj = self.getUnique(**self)
        if not obj:
            raise ValueError, "current object doesn't exist in database!"
        # the ordinary dict update needs to be called here, not the
        # overloaded method that updates the database!
        super(PyDO, self).update(obj)


    
    def joinTableSQL(self,
                     thisAttrNames,
                     pivotTable,
                     thisSideColumns,
                     thatSideColumns,
                     thatObject,
                     thatAttrNames,
                     extraTables = None):
        """Handle many to many relations.  In short, do a
        
        SELECT thatObject.getColumns(1)
        FROM thatObject.table, pivotTable
        WHERE pivotTable.thisSideColumn = self[myAttrName]
        AND pivotTable.thatSideColumn = thatObject.table.thatAttrName
        
        and return a list of thatObjects representing the resulting rows.
        """
        if extraTables is None:
            extraTables=[]
        
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
    



## BELOW ISN'T WORKED ON YET....

    def scatterFetchSQL(cls, objs):
        """ Select objects from multiple tables
        
        Do a scatter fetch (a select from more than one ta ble) based
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
    


def _tupleize(item):
    if type(item) == types.TupleType:
        return item
    return (item,)


    
__all__=['PyDO']
