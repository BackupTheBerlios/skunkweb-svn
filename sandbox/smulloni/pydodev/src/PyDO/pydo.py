try:
    set
except NameError:
    from sets import Set as set
    
from PyDO.field import Field, _fieldset
from PyDO.exceptions import PyDOError

class _metapydo(type):
    """metaclass for _pydobase"""
    
    def __init__(cls, cl_name, bases, namespace):
        # handle inheritance of (private) class attributes
        revbases=[x for x in bases[::-1] if x is not object]
        for a, t in (('_fields', fieldset),
                     ('_unique', set),
                     ('_sequenced', dict),
                     ('_auto_increment', dict)):
            setattr(cls, a, t())
            for b in revbases:
                o=getattr(b, a, None)
                if o:
                    # set, dict and fieldset all have update()
                    getattr(cls, a).update(o)
                    
        # add attributes declared for this class
        for f in cls.fields:
            # support for tuple syntax for plain Jane fields
            if not isinstance(f, Field):
                f=Field(*f)
            # add to field container
            cls._fields.register(f)

        # manage this class's declared attributes
        cls._unique.update(cls.unique)
        cls._sequenced.update(cls.sequenced)
        cls._auto_increment.update(cls.auto_increment)
        
        # add attribute access to fields
        if cls.use_attributes:
            for f in cls._fields:
                if not hasattr(cls, f.pyname):
                    # a field is also a descriptor
                    setattr(cls, f.pyname, f)


class PyDO(object):
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

    def __init__(self, adict):
        """Constructor.  Normally users don't use this directly,
        but obtain instances through class methods like new()
        and getSome().
        """
        self._dict=adict

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

    def _translate_key(cls, key):
        """translate pyname to dbname.  pyname must be valid for the class."""
        return cls._fields.pynames[key].dbname
    _translate_key=classmethod(_translate_key)

    def _reverse_translate_key(cls, key):
        """translate dbname to pyname.  dbname must be valid for the class."""        
        return cls._fields.dbnames[key].pyname
    _reverse_translate_key=classmethod(_reverse_translate_key)

    def _translate_dict(cls, adict):
        """translate a dict with pyname keys to a dict with dbname keys.
        The keys must be valid pynames for the class."""
        return dict([(cls._translate_key(k), v) for k, v in adict.iteritems()])

    def _translate_seq(cls, seq):
        """translate a sequence of pynames to a sequence of dbnames.
        The pynames must be valid for the class."""
        return map(cls._translate_key, seq)

    def __getitem__(self, key):
        """ Part of dictionary interface for field access"""
        return self._dict[key]
    
    def __setitem__(self, key, val):
        """ Part of dictionary interface for field access"""
        return self.update(key: val})
    
    def items(self):
        """ Part of dictionary interface for field access"""
        return self._dict.items()

    def __iter__(self):
        """Part of dictionary interface for field access"""
        return self._dict.__iter__()

    def iteritems(self):
        """Part of dictionary interface for field access"""
        return self._dict.iteritems()

    def itervalues(self):
        """Part of dictionary interface for field access"""
        return self._dict.itervalues()
    
    def has_key(self, key):
        """ Part of dictionary interface for field access"""
        return self._dict.has_key(key)
    
    def keys(self):
        """ Part of dictionary interface for field access"""                                             
        return self._dict.keys()
    
    def values(self):
        """ Part of dictionary interface for field access"""
        return self._dict.values()
    
    def get(self, key, default=None):
        """ Part of dictionary interface for field access"""
        return self._dict.get(key), default)
    
    def update(self, adict):
        """ Part of dictionary interface for field access"""
        # call (normally empty) hook for modifying the update   
        self.onUpdate(adict)
        # translate to real field names.  This also checks that the
        # fields in the dictionary kosher, and blows up otherwise.
        d=dict([(self._translate_key(k), v) for k, v in adict.iteritems()])
        # do the actual update
        self.updateRawValues(self, d)
        # if successful, modify the object's field data
        self._dict.update(adict)

    def onUpdate(self, adict):
        """a hook for subclasses to modify updates; by default does nothing."""
        pass

    def dictRaw(self):
        """ Returns a dict mapping unescaped field names to their current values."""
        return dict([(self._translate_key(k), v) for k, v in self._dict.iteritems()])

    def dict(self):
        
        """ Returns a dict mapping escaped field names to their current values.
        (Escaping consists of appending an underscore to a field name if
        the name is a Python keyword.)
        """
        return self._dict.copy()
    
    def copy(self):
        """  Part of dictionary interface for field access """     
        return self.__class__(self._dict.copy())
    
    def __cachekey__(self):
        """ Return a key to be used by skunkweb's caching mechanism.
        
        Skunkweb allows for caching components. Arguments to cached
        components must be hashable or (in case of classes you write
        yourself) implement a __cachekey__ method that returns
        something which can be used to uniquely identify it.
        
        Default is to return a dict representation of the instance.
        """
        return self._dict

    def getColumns(cls, qualified=False):
        """Returns a list of all columns in this table, in no particular order.

        If qualified is true, returns fully qualified column names
        (i.e., table.column)
        """
        if not qualified:
            return cls._fields.dbnames.keys()
        else:
            t=cls.table
            return ["%s.%s" % (t, x) for x in cls._fields.dbnames.iterkeys()]
    getColumns=classmethod(getColumns)

    def _validateFields(cls, adict):
        """a simple field validator that verifies that the keys
        in the dictionary passed are declared fields in the class.
        """
        for k in adict:
            if not cls._fields.pynames.has_key(k):
                raise KeyError, "object %s has no field %s" %\
                      (cls, k)
    _validateFields=classmethod(_validateFields)
        
    def _baseSelect(cls, qualified=False):
        return 'SELECT %s FROM %s' % (', '.join(cls.getColumns(qualified)),
                                      cls.table)
    _baseSelect=classmethod(_baseSelect)

    def new(cls, refetch = None, values=None, **kw):
        """create and return a new data class instance using the values in
        kw.  This will also effect an INSERT into the database.  If refetch
        is true, effectively do a getUnique on cls.
        """
        if not cls.mutable:
            raise ValueError, 'cannot make a new immutable object!'
        tkw = cls._translate_dict(kw)
        conn = cls.getDBI()
        
        extra = {}
        for s, sn in cls.sequenced.items():
            if not tkw.has_key(s):
                extra[s] = conn.getSequence(sn)
        tkw.update(extra)
        
        cols = []
        values = []
        vals = []
        atts = []
        for dbname, v in tkw.iteritems():
            cols.append(dbname)
            dbtype = cls._fields.typedict[dbname]
            atts.append(dbtype)
            lit, val = conn.sqlStringAndValue(v, dbname, dbtype)
            values.append(lit)
            vals.append(val)
        sql = 'INSERT INTO %s (%s) VALUES  (%s)' \
              % (cls.table,
                 ', '.join(cols),
                 ', '.join(values))
        res = conn.execute(sql, vals, cls._fields.typedict)
        if res != 1:
            raise PyDOError, "inserted %s rows instead of 1" % res
        
        if cls.auto_increment:
            for k, v in cls.auto_increment.items():
                if not tkw.has_key(k):
                    tkw[k] = conn.getAutoIncrement(v)
        
        conn.postInsertUpdate(cls, tkw, 1)
        if not refetch:
            return cls(tkw)
        return cls.getUnique(**tkw)

    new=classmethod(new)
    
    def getUnique(cls, **kw):
        """ Retrieve one particular instance of this class.
        
        Given the attribute/value pairs in kw, retrieve a unique row
        and return a data class instance representing said row or None
        if no row was retrieved.
        """
        tkw = cls._translate_dict(kw)
        
        unique = cls._matchUnique(tkw)
        sql = cls._baseSelect() + " WHERE "
        
        conn = cls.getDBI()
        where, values = cls._uniqueWhere(conn, tkw)
        sql = "%s WHERE %s" % (cls._baseSelect(), where)
        results = conn.execute(sql, values, cls._fields.typedict)
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
    
    def getSomeSQL(cls, **kw):
        """ Prepare the SQL required to retrieve some objects by keyword.
        
        Given the attribute/value pairs in kw, return
        sql statement, values to be used in a call to conn.execute.
        If kw is empty, the WHERE text in the sql statement will still
        be preseverved.
        """
        kw = cls._convertKW(kw)
        sql = cls._baseSelect() + " WHERE "
        conn = cls.getDBI()
        where = []
        values = []
        order = []
        limit = 0
        offset = 0
        key_count = 0
        for k, v in kw.items():
            if k == 'order':
                if type(v) == types.StringType:
                    order.append(v)
                else:
                    order.extend(v)
                continue
            elif k == 'limit':
                limit = v
                continue
            elif k == 'offset':
                offset = v
                continue
            else:
                key_count += 1
            lit, val = conn.sqlStringAndValue(v, k, cls.dbColumns[k])
            
            where.append("%s=%s" % (
            k, lit))
            values.append(val)
        
        if key_count != 0:
            sql = sql + ' AND '.join(where)
        else:
            sql = sql[:-7]
                
        if len(order):
            sql += cls._orderByString(order)
        
        if limit:
            sql = sql + ' LIMIT %d' % limit
            
        if offset:
            sql = sql + ' OFFSET %d' % offset 
            
        return sql, values
    getSomeSQL=classmethod(getSomeSQL)
    
    def getSome(cls, **kw):
        """ Retrieve some objects by keyword
        
        Given the attribute/value pairs in kw, return a (potentially
        empty) list of data class instances representing the rows that
        fulfill the constraints in kw
        """
        kw = cls._convertKW(kw)
        sql, values=cls.getSomeSQL(**kw)
        conn=cls.getDBI()
        results = conn.execute(sql, values, cls.dbColumns)
        if type(results)==types.ListType:
            return map(cls, results)
        else:
            return []
    getSome=classmethod(getSome)
    
    def class_getSomeWhere(cls, *args, **kw):
        """ Retrieve some objects of this particular class.
        
        Allows you to use the operator objects in PyDO.operators to be
        able to use sql operators other than the implicit AND as
        used by the other static get methods.
        
        The **kw argument is the same as the other static get methods.
        The *args argument however allows you to combine operators to
        do operations like OR, NOT, LIKE, etc. For example, the following
        would get all rows where the last name field was LIKE Ingers%.
        
        obj.getSomeWhere(LIKE(FIELD('last_name'), ('Ingers%')))
        
        """
        kw = cls._convertKW(kw)
        andValues=list(args)
        for k, v in kw.items():
            if k not in ('order', 'offset', 'limit'):
                andValues.append(operators.EQ(operators.FIELD(k), v))
        andlen=len(andValues)
        if andlen > 1:
            daOp=operators.AND(*andValues)
        elif andlen==1:
            daOp=andValues[0]
        else:
            daOp=None
        sql=(daOp and daOp.asSQL()) or ''
        
        order=[]
        limit=0
        offset=0
        if kw.get('order'):
            if type(kw['order']) == types.StringType:
                order.append(kw['order'])
            else:
                order.extend(kw['order'])
        if kw.get('limit'):
            limit = kw['limit']
        if kw.get('offset'):
            offset = kw['offset']
        
        return cls.getSQLWhere(sql, order=order, limit=limit, offset=offset)
    
    def class_getTupleWhere(cls, opTuple, order=(), limit=0, offset=0, **kw):
        """ Retrieve objects using Lisp-like queries
        
        Allows you to use a somewhat Lispish notation for generating
        SQL queries, like so:
        
        obj.getTupleWhere(('OR', 
        ('LIKE', FIELD('last_name'), 'Ingers%'), 
        ('OR', ('<>', FIELD('id'), 355),
        ('=', FIELD('id'), 356))))
        
        Strings are used to represent operators rather than the SQLOperator
        class wrappers used in getSomeWhere(), but the FIELD and SET classes
        are still useful. The kw argument is treated the same as in
        getSome() and getSomeWhere().
        
        """
        kw = cls._convertKW(kw)
        
        if kw:
            _and=opTuple and ['AND', opTuple] or []
            for k, v in kw.items():
                _and.append(('=', FIELD(k), v))
            opTuple=tuple(_and)
        sql=opTuple and operators.tupleToSQL(opTuple) or ''
        
        order_list=[]

        if order:
            if type(order) == types.StringType:
                order_list.append(order)
            else:
                order_list.extend(order)        
        
        return cls.getSQLWhere(sql, order=order_list, limit=limit, offset=offset)
    
    def class_getSQLWhere(cls, sql, values=(), order=(), limit=0, offset=0):
        """ Retrieve objects with custom 'where' clause.
        
        Executes a sql statement to fetch the object type where
        you supply the where clause (without the WHERE keyword) and
        values in the case that you bind variables.
        """
        base=cls._baseSelect()
        if sql:
            sql="%s WHERE %s" % (base, sql)
        else:
            sql=base

        if len(order):
            sql += cls._orderByString(order)
        if limit:
            sql += ' LIMIT %d' % limit
        if offset:
            sql += ' OFFSET %d' % offset

        conn = cls.getDBI()
        results = conn.execute(sql, values, cls.dbColumns)
        if results and type(results)==types.ListType:
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
            obj.dbColumns,
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
            lit, val = conn.sqlStringAndValue(v, k, cls.dbColumns[k])
            
            where.append("%s.%s %s= %s" % (
            cls.table, k, notFlag, lit))
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
            dbtype = self._fields.dbnames[dbname].dbtype
            conn.typeCheckAndConvert(v, dbname, dbtype)
            lit, val = conn.sqlStringAndValue(v, dbname, dbtype)
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
