from pydo.field import Field

try:
    set
except NameError:
    from sets import Set as set

class _fieldproperty(object):
    __slots__=('_fieldname',)
    
    def __init__(self, fieldname):
        self._fieldname=fieldname
        
    def __get__(self, obj, tipe):
        return obj[self._fieldname]
    
    def __set__(self, obj, value):
        return obj.update[{self._fieldname:value}]

class _metapydo(type):
    """metaclass for _pydobase"""
    def __init__(cls, cl_name, bases, namespace):

        cls._field_dict={}
        cls._unique=set()
        cls._sequenced={}
        cls._auto_increment={}
        
        for b in bases:
            if hasattr(b, '_field_dict'):
                cls._field_dict.update(b._field_dict)
            if hasattr(b, '_unique'):
                cls._unique.update(b._unique)
            if hasattr(b, '_sequenced'):
                cls._sequenced.update(b._sequenced)
            if hasattr(b, '_auto_increment'):
                cls._auto_increment.update(b._auto_increment)
        
        for f in cls.fields:
            if not isinstance(f, Field):
                f=Field(*f)
            self._field_dict[f.dbname]=f

        cls._unique.update(cls.unique)
        cls._sequenced.update(cls.sequenced)
        cls._auto_increment.update(cls.auto_increment)
        cls._dbcolumns = {}
        for field in cls._field_dict.itervalues():
            cls._dbcolumns[field.dbname]] = field.dbtype
            if cls.use_attributes and not hasattr(cls, field.name):
	        setattr(cls, field.name, _fieldproperty(field.name))


class _pydobase(object):
    """ Baseclass for PyDO.
    
    _pydobase implements most of the generic functionality to make
    persistent PyDO-instances behave like normal Python
    classes/object.
    
    Not meant to be uses directly. Inherit from PyDO instead.
    """
    __metaclass__=_metapydo

    table=None
    mutable=1
    use_attributes=1
    connAlias=None
    fields=()
    unique=[]
    sequenced={}
    auto_increment={}


    def __init__(self, adict):
        self._dict=adict


    def getDBI(klass):
        """return the database interface
        """
        conn=DBIGetConnection(klass.connectionAlias)
        conn.resetQuery()
        return conn
    getDBI=classmethod(getDBI)


    def commit(klass):
        """ Commit changes to database
        """
        return klass.getDBI().commit()
    commit=classmethod(commit)


    def rollback(klass):
        """ Rollback current transaction
        """
        return klass.getDBI().rollback()
    rollback=classmethod(rollback)
    
    def __getitem__(self, item):
        """ Part of dictionary interface for field access
        """
        return self._dict[self.fieldDict[item]['dbName']]
    
    def __setitem__(self, item, val):
        """ Part of dictionary interface for field access
        """
        return self.update({item: val})
    
    def items(self):
        """ Part of dictionary interface for field access
        """             
        return self._dict.items()
    
    def has_key(self, key):
        """ Part of dictionary interface for field access
        """                             
        key = self.fieldDict[key]['dbName']
        return self._dict.has_key(key)
    
    def keys(self):
        """ Part of dictionary interface for field access
        """                                             
        return self.fieldDict.keys()
    
    def values(self):
        """ Part of dictionary interface for field access
        """                                             
        return self._dict.values()
    
    def get(self, item, default=None):
        """ Part of dictionary interface for field access
        """                             
        key = self.fieldDict[item]['dbName']
        return self._dict.get(key, default)
    
    def update(self, adict):
        """ Part of dictionary interface for field access
        """                             
        #print "Update is called with: %s" % adict
        bdict = {}
        for k in adict:
            try:
                bdict[self.fieldDict[k]['dbName']] = adict[k]
            except KeyError:
                raise KeyError, "object %s has no field %s" \
                      % (self.__class__, k)
            self.updateValues(adict)
            self._dict.update(bdict)
    
    def updateValues(self, adict):
        """ Updates underlying database table
        
        Called whenever fields are updated.
        
        If you want to have some fields changed
        automatically on update (e.g. a 'lastmodified'
        timestamp), you can do that by overriding this
        method.
        
        Don't forget to call the parents updateValues
        when you're done, or nothing gets updated
        at all!
        
        """
        raise NotImplementedError, "no way to update"
    
    def dict(self):
        """ Returns a dictionary containing of all fields
        """
        return self._dict.copy()
    
    def copy(self):
        """  Part of dictionary interface for field access
        """     
        return self.__class__(self._dict.copy())
    
    def __cachekey__(self):
        """ Return a key to be used by skunkwebs caching mechanism.
        
        Skunkweb allows for caching components. Arguments to
        cached components must be hashable or (in case of
        classes you write yourself) implement a __cachekey__
        method that returns something which can be used
        to uniquely identify it.
        
        Default is to return a dict representation of the
        instance.
        
        If you plan on using a particular class in combination
        with cached components, it is probably a wise thing to
        include a 'lastmodified' field that is automatically
        updated everytime the object changes (by overriding
        updateValues).
        
        This is because when the called component changes
        the object, you will find that it changes only the first time
        the component is called, becuase on subequent calls, the output
        is cached and the component will not be executed.
        """
        return self._dict

            sql=base

        if len(order):
            sql += klass._orderByString(order)
        if limit:
            sql += ' LIMIT %d' % limit
        if offset:
            sql += ' OFFSET %d' % offset

        conn = klass.getDBI()
        results = conn.execute(sql, values, klass.dbColumns)
        if results and type(results)==types.ListType:
            return map(klass, results)
        else:
            return []


    def scatterFetchSQL(klass, objs):
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
        objs = ((klass, None, None, None),) + tuple(objs)
        cols = []
        for obj in objs:
            cols.extend(obj[0].getColumns(1))
        tabs = map(lambda x:x[0].getTable(), objs)
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
                    j.append('%s.%s = %s.%s' % (obj.getTable(), klass.fieldDict[attri]['dbName'],
                    dobj.getTable(), klass.fieldDict[dattri]['dbName']))
                
            else:
                if dobj:
                    j.append('%s.%s = %s.%s' % (obj.getTable(), klass.fieldDict[attr]['dbName'],
                    dobj.getTable(), klass.fieldDict[dattr]['dbName']))
        sql = sql + ' AND '.join(j)
        return sql, cols, objs
    scatterFetchSQL=classmethod(scatterFetchSQL)


    def scatterFetchPost(klass, objs, sql, vals, cols):
        """handle the execution and processing of a scatter fetch to produce
        a result list -- returns the list of tuples referred to in the
        docstring of scatterFetchSQL"""
        conn = klass.getDBI()
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
    
    def scatterFetch(klass, objs, **kw):
        """see scatterFetchSQL for format of objs and getSome for format
        of **kw
        """
        
        sql, cols, objs = klass.scatterFetchSQL(objs)
        
        conn = klass.getDBI()
        where = []
        values = []
        for k, v in kw.items():
            notFlag = ''
            if isinstance(v, NOT):
                notFlag = '!'
                v = v.val
            lit, val = conn.sqlStringAndValue(v, k, klass.dbColumns[k])
            
            where.append("%s.%s %s= %s" % (
            klass.getTable(), k, notFlag, lit))
            values.append(val)
        whereClause = ' AND '.join(where)
        if whereClause:
            sql = sql + " AND " + whereClause
        
        #make where clause here from **kw
        return klass.scatterFetchPost(objs, sql, values, cols)
    scatterFetch=classmethod(scatterFetch)
    
    ##############################
    ## Public instance methods
    ##############################
    
    def updateValues(self, dict):
        """update self in database with the values in dict"""
        if not self.mutable:
            raise ValueError, "instance isn't mutable!"
        sql = "UPDATE %s SET " % self.getTable()
        sets = []
        values = []
        conn = self.getDBI()
        atts = []
        
        for k, v in dict.items():
            fieldName = self.fieldDict[k]['dbName']
            fieldType = self.fieldDict[k]['dbType']
            conn.typeCheckAndConvert(v, fieldName, fieldType)
            lit, val = conn.sqlStringAndValue(v, fieldName, fieldType)
            atts.append(fieldType)
            values.append(val)
            sets.append("%s = %s" % (fieldName, lit))
        
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
        sql = 'DELETE FROM %s WHERE %s' % (self.getTable(), unique)
        conn.execute(sql, values, self.dbColumns)
        self.mutable = 0
    
    def refresh(self):
        """refetch myself from the database"""
        obj = apply(self.getUnique, (), self._dict)
        if not obj:
            raise ValueError, "current object doesn't exist in database!"
        #        mutable = self.mutable #save if was deleted, it still is deleted
        self._dict = obj._dict
    #        self.mutable = self._klass.mutable
    
    def joinTableSQL(self, thisAttrNames, pivotTable, thisSideColumns,
        thatSideColumns, thatObject, thatAttrNames,
        extraTables = []):
        """Handle many to many relations.  In short, do a
        
        SELECT thatObject.getColumns(1)
        FROM thatObject.getTable(), pivotTable
        WHERE pivotTable.thisSideColumn = self[myAttrName]
        AND pivotTable.thatSideColumn = thatObject.getTable().thatAttrName
        
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
        thatTable = thatObject.getTable()
        for attr, col in map(None, thatAttrNames, thatSideColumns):
            thatJoin.append('%s.%s = %s.%s' % (pivotTable,
                                               col,
                                               thatTable,
                                               attr))
        
        sql = '%s%s' % (sql, ' AND '.join(thatJoin))
        return sql, vals
    
    
    def joinTable(self, thisAttrNames, pivotTable, thisSideColumns,
        thatSideColumns, thatObject, thatAttrNames):
        """see joinTableSQL for arguments
        
        This method executes the statement returned by joinTableSQL with
        the arguments and produces object from them.
        """
        conn = self.getDBI()
        sql, vals = self.joinTableSQL(thisAttrNames, pivotTable,
        thisSideColumns, thatSideColumns,
        thatObject, thatAttrNames)
        results = conn.execute(sql, vals, thatObject.dbColumns)
        return map(thatObject, results)        
    
    
    ####################################################
    ##
    ## Private methods start here
    ##
    ## Following methods are not part of the public
    ## interface.
    ##
    ##
    @classmethod
    def validateFields(klass, dict):
        """a simple field validator, basically checks to see that
        you don't try to set fields that don't exist."""
        for k in dict.keys():
            if not klass.fieldDict.has_key(k):
                raise KeyError, 'object has no field %s' % k

    @classmethod
    def _baseSelect(klass, qualified=None):
        sql='SELECT %s FROM %s' % (', '.join(klass.getColumns(qualified)),
        klass.table)
        return sql
    
    @classmethod
    def _matchUnique(klass, kw):
        """return a tuple of column names that will uniquely identify
        a row given the choices from kw"""
        for unique in klass._unique:
            if isinstance(unique, str):
                if kw.has_key(unique) and kw[unique] is not None:
                    return (unique,)
            elif isinstance(unique, tuple):
                for u in unique:
                    if not kw.has_key(u):
                        break
                else:
                    return unique
    
    @classmethod
    def _uniqueWhere(klass, conn, kw):
        """given a connection and kw, using _matchUnique, generate a
        where clause to select a unique row.
        """
        unique = klass._matchUnique(kw)
        if not unique:
            raise ValueError, 'No way to get unique row! %s %s' % (
            str(kw), unique)
        
        where = []
        values = []
        for u in unique:
            lit, val = conn.sqlStringAndValue(kw[u], u, klass.dbColumns[u])
            where.append("%s = %s" % (u, lit))
            values.append(val)
        return ' AND '.join(where), values
    
    # following two methods are helper functions to convert
    # either a dict or a tuple containing Python attribute names
    # into their corresponding database column names. This is
    # to allow a difference between attribute name and column
    # name without putting the burden of conversion on the
    # developer.
    
    # for tuples, used in scatterFetch etc.
    @classmethod
    def _convertTupleKW(klass, tup):
        nt = []
        for i in tup:
            try:
                nt.append(klass.fieldDict[i]['dbName'])
            except KeyError:
                # apparently already converted
                # or just bogus. Neither way should we
                # worry about it here. Return original
                # input and let it (perhaps) go wrong
                # somewhere else.
                return tup
        return tuple(nt)
    
    # for dicts, used in getSome, getUnique etc.
    @classmethod
    def _convertKW(klass, kw):
        nkw = {}
        for k, v in kw.iteritems():
            try:
                nkw[klass.fieldDict[k]['dbName']] = v
            except KeyError:
                # apparently already converted
                # or just bogus. Neither way should we
                # worry about it here. Return original
                # input and let it (perhaps) go wrong
                # somewhere else. 
                return kw
        return nkw


def _tupleize(item):
    if type(item) == types.TupleType:
        return item
    return (item,)



# 2003-10-20 
#   Brian Olsen <brian@qinternet.com>
#
# Added the offset, limit, and order parameters to getSome(), getSomeSQL()
# getTupleWhere(), getSomeWhere(), and getSQLWhere(). A PyDO statement like
# this:
#
# MyTable.getSome(id=1, order=('id',), limit=1, offset=2)
#
# will produce something like this:
#
# SELECT id FROM my_table WHERE id=1 ORDER BY id LIMIT 1 OFFSET 2
#
# 2003-08-24 several modifications by:
#   Jacob Smullyan <smulloni@smullyan.org>
#   Jeroen van Dongen <jeroen@vthings.net>
#
# Following modifications are made in an effort to
# make PyDO's more like regular Python classes:
#
# - The static module is no longer used. PyDO classes are now
#   regular Python classes.
# - mro matches the mro for Python new-style classes
#   So diamond-shaped class hierarchies are possible (although
#   I'm not sure how to reflect that in SQL, but that's your
#   problem :-). 
# - Fields can be accessed either dictionary-style or
#   attribute-style
# - The name of the field in the database may differ from the
#   Python attribute name (hence you can have database fields with names like
#   'pass', 'class', etc.)
# - It is now possible to associate other attributes with a
#   a field, besides its database-type
#
# The following modifications are still on the wishlist:
# - it should work in multithreaded environments;
#   review assumptions made about drivers.
#   [JvD: probably best is to just use a multithread-aware driver, such
#    as Psycopg?]
# - it should be possible to get a subclass of an object
#   to have a subset of the full list of fields.
#   [JvD: perhaps drop requirement? Or create a method which fetches
#    only a few attributes, based on a getUnique?]
#

                
    
