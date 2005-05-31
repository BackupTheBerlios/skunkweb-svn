from pydo.dbi import getConnection
from pydo.field import Field
from pydo.exceptions import PyDOError
from pydo.operators import AND, EQ, FIELD
from pydo.dbtypes import unwrap
from pydo.utils import _tupleize, _setize, formatTexp, _strip_tablename

from itertools import izip

def _restrict(flds, coll):
    """private method for cleaning a set or dict of any items that aren't
    in a field list (or dict); needed for handling attribute inheritance
    for projections"""
    
    # handle sets (_unique).  Sets may contain groupings of fieldnames
    # for multi-column unique constraints; this tests each member of
    # the grouping (sets, frozensets, lists, and tuples are tolerated)
    
    if isinstance(coll, set):
        s=set()
        for v in coll:
            # this isn't where the type of the set element
            # is enforced
            if isinstance(v, (set, frozenset, tuple, list)):
                for v1 in v:
                    if v1 not in flds:
                        break
                    else:
                        # (added just to make indentation clearer)
                        continue
                else:
                    # if we get here, the fields in the
                    # grouping are in the projection
                    s.add(v)
            elif v in flds:
                s.add(v)
        return s
    # It isn't necessary to test for multi-column keys in dicts
    elif isinstance(coll, dict):
        return dict((x, y) for x, y in coll.iteritems() if x in flds)

class _metapydo(type):
    """metaclass for _pydobase.
    Manages attribute inheritance.
    """

    def __init__(cls, cl_name, bases, namespace):
        # tablename guessing
        if not namespace.has_key('table') and cls.guess_tablename:
            cls.table=cl_name.lower()
        # field guessing
        if namespace.get('guess_columns', False):
            if 'fields' in namespace or 'unique' in namespace:
                raise ValueError, ("incompatible declarations: guess_columns "
                                   "with explicit declaration of fields and/or unique")
            gfields, gunique=cls._getTableDescription()
            namespace['fields']=gfields.values()
            namespace['unique']=gunique

        # create Field objects declared locally in this class
        # and store them in a temporary dict
        fielddict={}
        # we keep track of which fields are declared just with a string;
        # inheritance semantics are a little different for these
        simplefields=set()
        for f in namespace.get('fields', ()):
            # support for tuple syntax for plain Jane fields.
            if isinstance(f, basestring):
                simplefields.add(f)                
                f=cls._create_field(f)
            elif isinstance(f, dict):
                f=cls._create_field(**f)
            elif isinstance(f, (tuple, list)):
                f=cls._create_field(*f)
            elif not isinstance(f, Field):
                raise ValueError, "cannot coerce into a field: %s" % f
                
            # add to field container
            fielddict[f.name]=f

        # handle inheritance of fields and unique declarations.
        # skipping object and dict is a trivial optimization,
        # because we know those classes won't be relevant
        revbases=[x for x in bases[::-1] if x not in (object, dict)]

        cls._fields={}
        uniqueset=set()
        for b in revbases:
            flds=getattr(b, '_fields', None)
            if flds:
                if cls._is_projection:
                    flds=_restrict(fielddict, flds)
                cls._fields.update(flds)
            uniq=getattr(b, 'unique', None)
            if uniq:
                # transform into a set of sets.  This way,
                # multi-column unique constraints are
                # unordered.
                uniq=set(_setize(x) for x in uniq)
                if cls._is_projection:
                    uniq=_restrict(fielddict, uniq)
                uniqueset.update(uniq)

        # If a field is declared upstream and you redeclare it in a
        # subclass as a simple field (just a fieldname), then the
        # previous field definition is inherited; otherwise, the
        # subclass's definition wins.  This is useful for projections.
        updatefields=((x, y) for x, y in fielddict.iteritems() \
                      if not (x in cls._fields and x in simplefields))
        cls._fields.update(updatefields)
        uniqueset.update(_setize(x) for x in namespace.get('unique', ()))

        # We now have all the inherited declarations, and figure out
        # sequences and additional unique constraints.
        cls._sequenced={}
        for f in cls._fields.itervalues():
            if f.sequence:
                cls._sequenced[f.name]=f.sequence
            if f.unique:
                uniqueset.add(frozenset((f.name,)))

        cls._unique=frozenset(uniqueset)

        # add attribute access to fields
        if cls.use_attributes:
            for name in cls._fields:
                if not hasattr(cls, name):
                    # a field is also a descriptor
                    setattr(cls, name, cls._fields[name])
        
class PyDO(dict):
    """ Base class for PyDO data classes."""

    __metaclass__=_metapydo

    # subclasses may customize these
    guess_tablename=True
    guess_columns=False
    use_attributes=True
    mutable=True
    connectionAlias=None
    table=None
    schema=None
    refetch=False
    
    ## not defined by default, but if you aren't using guess_columns
    ## you'll want to define it at some point in your class hierarchy
    # fields 

    # private - don't touch
    _projections={}
    _is_projection=False

    @classmethod
    def _getTableDescription(cls):
        """ supplies the table fields (as a dict of fieldnames to Field objects)
	and a list of multi-column unique constraints to the metaclass, which will
	call it when guessing columns.  By default this delegates to the DBI driver 
	and performs no caching; if you want to cache it (to a file, presumably, since
	it will only get called once per process anyway, at class creation time) this
	is the hook to do it.
	"""
	return cls.getDBI().describeTable(cls.getTable(False), cls.schema)
    
    @staticmethod
    def _create_field(*args, **kwargs):
        """ controls how fields are created when declared in the field
        list with a simple string, list, tuple, or dictionary rather
        than a field instance.  By default, passes field declaration
        to the Field constructor.
        """
        
        return Field(*args, **kwargs)

    @classmethod
    def getTable(cls, withSchema=True):
        """returns the name of the table, qualified with the schema,
        if any, if withSchema is true.
        """
       
        if cls.schema and withSchema:
            return '%s.%s' % (cls.schema, cls.table)
        else:
            return cls.table


    @classmethod
    def project(cls, fields):
        s=[]
        for f in fields:
            if isinstance(f, Field):
                s.append(f.name.lower())
            elif isinstance(f, basestring):
                s.append(f.lower())
            elif isinstance(f, tuple):
                if not len(f):
                    raise ValueError, "empty tuple in field list"
                s.append(f[0].lower())
            else:
                raise ValueError, "weird thing in field list: %s" % f
        s.sort()
        t=tuple(s)
        if cls._projections.has_key(t):
            return cls._projections[t]
        klsname='projection_%s__%s' % (cls.__name__,
                                       '_'.join(s))
        kls=type(klsname, (cls,), dict(fields=fields,
                                       table=cls.getTable(False),
                                       _is_projection=True))
        cls._projections[t]=kls
        return kls


    def update(self, adict):
        """ Part of dictionary interface for field access"""
        if not self.mutable:
            raise ValueError, "instance isn't mutable!"
        if not self._unique:
            raise ValueError, "cannot update without unique index!"
        # call (normally empty) hook for modifying the update
        d=self.onUpdate(adict)
        # Check that the fields in the dictionary are kosher
        self._validateFields(d)
        # do the actual update
        self._update_raw(d)
        # if successful, modify the object's field data,
        # taking any wrapped values out of their wrappers
        unwrapped=dict((k, unwrap(v)) for k,v in d.iteritems())
        super(PyDO, self).update(unwrapped)

    def onUpdate(self, adict):
        """a hook for subclasses to modify updates; 
        by default returns the original data unchanged."""
        return adict

    def __setitem__(self, k, v):
        self.update({k:v})

    def _update_raw(self, adict):
        """update self in database with the values in adict"""

        # precondition: fields in adict are already validated,
        # and class/instance is mutable

        conn=self.getDBI()
        converter=conn.getConverter()
        sqlbuff=["%s  = %s" % (x, converter(y)) for x, y in adict.iteritems()]
        # pass in the same converter so that we don't get generated
        # interpolation names that clobber any others
        where, values=self._uniqueWhere(conn, self, converter)
        sql = "UPDATE %s SET %s WHERE %s" % (self.getTable(),
                                             ", ".join(sqlbuff),
                                             where)
        result=conn.execute(sql, values)
        if result > 1:
            raise PyDOError, "updated %s rows instead of 1" % result        

    @classmethod
    def updateSome(cls, adict, *args, **fieldData):
        """update possibly many records at once, and return the number updated"""
        if not cls.mutable:
            raise ValueError, "class isn't mutable!"
        # N.B. it *is* possible to use this method without a unique index
        if not adict:
            # vacuous update, just return
            return
        cls._validateFields(adict)
        conn=cls.getDBI()
        converter=conn.getConverter()
        sqlbuff=["UPDATE ",
                 cls.getTable(),
                 " SET ",
                 ', '.join(["%s = %s" % (x, converter(y)) \
                            for x, y in adict.iteritems()])]
        #values=converter.values
        where, values=cls._processWhere(conn, args, fieldData, converter)
        if where:
            sqlbuff.extend([' WHERE ', where])
            #values+=wvals
        return conn.execute(''.join(sqlbuff), values)


    def dict(self):
        """returns a copy of self as a plain dict"""
        return dict(self)

    def copy(self):
        """returns a copy of self"""
        return self.__class__(dict(self))
    
    def clear(self):
        """not implemented for PyDO classes"""
        raise NotImplementedError, "PyDO classes don't implement clear()"

    def pop(self):
        """not implemented for PyDO classes"""
        raise NotImplementedError, "PyDO classes don't implement pop()"

    def popitem(self):
        """not implemented for PyDO classes"""
        raise NotImplementedError, "PyDO classes don't implement popitem()"

    def setdefault(self, key, val):
        """not implemented for PyDO classes"""
        raise NotImplementedError, "PyDO classes don't implement setdefault()"
    
    @classmethod
    def getColumns(cls, qualifier=None):
        """Returns a list of all columns in this table, in no
        particular order.

        If qualifier is true, returns fully qualified column names
        (i.e., table.column).  If you pass in a string to qualifier,
        it will be used as a table alias; otherwise the table name
        will be used.
        
        """
        if not qualifier:
            return cls._fields.keys()
        else:
            if not isinstance(qualifier, basestring):
                qualifier=cls.getTable()
            return ["%s.%s" % (qualifier, x) for x in cls._fields.iterkeys()]

    @classmethod
    def getFields(cls):
        """returns the effective fields of the class"""
        return cls._fields.copy()

    @classmethod
    def getUniquenessConstraints(cls):
        """returns the effective uniqueness constraints of the class"""
        return cls._unique

    @classmethod
    def getSequences(cls):
        """returns the effective sequences for the class"""
        return cls._sequenced.copy()


    @classmethod
    def _validateFields(cls, adict):
        """a simple field validator that verifies that the keys
        in the dictionary passed are declared fields in the class.
        """
        for k in adict:
            if not cls._fields.has_key(k):
                raise KeyError, "object %s has no field %s" %\
                      (cls, k)

    # DB interface
    @classmethod
    def getDBI(cls):
        """return the database interface"""
        conn=getConnection(cls.connectionAlias)
        return conn

    @classmethod
    def commit(cls):
        """ Commit changes to database"""
        cls.getDBI().commit()

    @classmethod
    def rollback(cls):
        """ Rollback current transaction"""
        cls.getDBI().rollback()

    @classmethod
    def new(cls, **fieldData):
        """create and return a new data class instance using the
        values in fieldData.  This will also effect an INSERT into the
        database.  If the keyword argument refetch is passed and is true,
        or, if it is not and cls.refetch is true, effectively do a getUnique
        on cls.  """
        if 'refetch' in cls._fields:
            # don't use refetch keyword
            refetch=cls.refetch
        elif 'refetch' in fieldData:
            refetch=fieldData.pop('refetch')
        else:
            refetch=cls.refetch
        return cls._new(fieldData, refetch)

    @classmethod
    def newfetch(cls, **fieldData):
        """like new(), but always refetches."""
        return cls._new(fieldData, 1)

    @classmethod
    def newnofetch(cls, **fieldData):
        """like new(), but never refetches."""
        return cls._new(fieldData, 0)

    @classmethod
    def _new(cls, fieldData, refetch):
        if not cls.mutable:
            raise ValueError, 'cannot make a new immutable object!'
        if refetch and not cls._unique:
            raise ValueError, "cannot refetch without a unique index!"
        # sanity check the field data
        cls._validateFields(fieldData)
        
        conn = cls.getDBI()

        if not conn.auto_increment:
            for s, sn in cls._sequenced.items():
                if not fieldData.has_key(s):
                    fieldData[s] = conn.getSequence(sn)
        cols=fieldData.keys()
        vals=[fieldData[c] for c in cols]
        converter=conn.getConverter()
        converted=map(converter, vals)
        
        sql = 'INSERT INTO %s (%s) VALUES  (%s)' \
              % (cls.getTable(),
                 ', '.join(cols),
                 ', '.join(converted))
        res = conn.execute(sql, converter.values)
        if res != 1:
            raise PyDOError, "inserted %s rows instead of 1" % res
        
        if conn.auto_increment:
            for k, v in cls._sequenced.items():
                if not fieldData.has_key(k):
                    fieldData[k] = conn.getAutoIncrement(v)
        # unwrap any wrapped values in fieldData
        fieldData=dict((k, unwrap(v)) for k,v in fieldData.iteritems())
        if not refetch:
            return cls(fieldData)
        return cls.getUnique(**fieldData)

    @classmethod
    def _matchUnique(cls, kw):
        """return a tuple of column names that will uniquely identify
        a row given the choices from kw
        """
        for unique in cls._unique:
            if isinstance(unique, basestring):
                if kw.get(unique)!=None:
                    return (unique,)
            elif isinstance(unique, (frozenset,list,tuple)):
                for u in unique:
                    if not kw.has_key(u):
                        break
                else:
                    return unique

    @classmethod
    def _uniqueWhere(cls, conn, kw, converter=None):
        """given a connection and kw, using _matchUnique, generate a
        where clause to select a unique row.
        """
        unique = cls._matchUnique(kw)
        if not unique:
            raise ValueError, 'No way to get unique row! %s %s' % \
                  (str(kw), unique)
        if converter is None:
            converter=conn.getConverter()        
        if len(unique)==1:
            u=tuple(unique)[0]
            sql=str(EQ(FIELD(u), kw[u], converter=converter))
        else:
            sql=str(AND(converter=converter, *[EQ(FIELD(u), kw[u]) for u in unique]))
        return sql, converter.values

    
    @classmethod
    def getUnique(cls, **fieldData):
        """ Retrieve one particular instance of this class.
        
        Given the attribute/value pairs in fieldData, retrieve a unique row
        and return a data class instance representing said row or None
        if no row was retrieved.
        """
        cls._validateFields(fieldData)
        conn = cls.getDBI()
        where, values = cls._uniqueWhere(conn, fieldData)
        sql = "%s WHERE %s" % (cls._baseSelect(), where)
        results = conn.execute(sql, values)
        if not results or not isinstance(results, (list,tuple)):
            return
        if len(results) > 1:
            raise PyDOError, 'got more than one row on unique query!'
        if results:
            return cls(results[0]) 

    @classmethod
    def _baseSelect(cls, qualified=False):
        """returns the beginning of a select statement for this object's table."""
        return 'SELECT %s FROM %s' % (', '.join(cls.getColumns(qualified)),
                                      cls.getTable())


    @staticmethod
    def _processWhere(conn, args, fieldData, converter=None):
        if args and isinstance(args[0], basestring):
            if fieldData:
                raise ValueError, "cannot pass keyword args when including sql string"
            sql=args[0]
            values=args[1:]

            if len(values)==1 and isinstance(values[0], dict):
                values=values[0]
        else:
            # no longer require fields expressed as keyword arguments to be
            # declared in the class/projection.
            #cls._validateFields(fieldData)
            andValues=list(args)
            # why was I using a converter here???
            #tmpconverter=conn.getConverter()
            for k, v in fieldData.items():
                andValues.append(EQ(FIELD(k), v)) #, converter=tmpconverter))
            andlen=len(andValues)
            ## discard converter.values, we'll regenerate that next
            #converter.reset()
            if converter is None:
                converter=conn.getConverter()
            if andlen==0:
                sql=''
            elif andlen==1:
                andValues[0].converter=converter
                sql=repr(andValues[0])
            else:
                sql=repr(AND(converter=converter, *andValues))
            values=converter.values
        return sql, values


    @classmethod
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
        sql, values=cls._processWhere(conn, args, fieldData)
        query=[cls._baseSelect()]
        if sql:
            query.extend(['WHERE', sql])
        if filter(None, (order, limit, offset)):
            query.append(conn.orderByString(order, limit, offset))
        query=' '.join(query)

        results = conn.execute(query, values)
        if results and isinstance(results, list):
            return map(cls, results)
        else:
            return []


    @classmethod
    def deleteSome(cls, *args, **fieldData):
        """delete possibly many records at once, and return the number deleted"""
        if not cls.mutable:
            raise ValueError, "cannot deleteSome through an immutable class"
        conn=cls.getDBI()
        sql, values=cls._processWhere(conn, args, fieldData)
        query=["DELETE FROM %s" % cls.getTable()]
        if sql:
            query.extend(['WHERE', sql])
        return conn.execute(' '.join(query), values)

    def delete(self):
        """remove the row that represents me in the database"""
        if not self.mutable:
            raise ValueError, "instance isn't mutable!"
        if not self._unique:
            raise ValueError, "cannot delete, no unique index!"
        conn = self.getDBI()
        unique, values = self._uniqueWhere(conn, self)
        # if the class has unique constraints, and all data
        # is presented, there will be something returned from
        # unique unless someone is doing bad things to the
        # object 
        assert unique
        sql = 'DELETE FROM %s WHERE %s' % (self.getTable(), unique)
        conn.execute(sql, values)
        # shadow the class attribute with an instance attribute
        self.mutable = False

    def refresh(self):
        """refetch myself from the database"""
        if not self._unique:
            raise ValueError, "cannot refresh without a unique index"
        obj = self.getUnique(**self)
        if not obj:
            raise ValueError, "current object doesn't exist in database!"
        # the ordinary dict update needs to be called here, not the
        # overloaded method that updates the database!
        super(PyDO, self).update(obj)


    def joinTable(self,
                  thisAttrNames,
                  pivotTable,
                  thisSideColumns,
                  thatSideColumns,
                  thatObject,
                  thatAttrNames,
                  *whereArgs,
                  **extra):

        """Handles many to many relations.  In short, do:
        
        SELECT thatObject.getColumns(1)
        FROM thatObject.table, pivotTable
        WHERE pivotTable.thisSideColumn = self.myAttrName
        AND pivotTable.thatSideColumn = thatObject.table.thatAttrName
        
        and return a list of thatObjects representing the resulting
        rows.  The parameters which accept column names
        (thisAttrNames, thisSideColumns, thatSideColumns,
        thatAttrNames) can be strings (silently turned to tuples of
        length 1) or tuples of strings.  For each pair P of the two
        pairs (thisSideColumns, thisAttrNames) and (thatSideColumns,
        thatAttrNames) len(P[0]) must equal len(P[1]).

        In addition, you can add extra tables and arbitrary sql to the
        where clause, as you can with getSome(), including order,
        limit and offset, using the "extraTables", "order", "limit"
        and "offset" keyword arguments, using SQLOperators or
        (sql-string, bind values) as positional arguments, and by
        specifying columns by keyword argument.
        
        """
        extraTables=extra.pop('extraTables', None)
        if extraTables:
            extraTables=list(_tupleize(extraTables))
        order=extra.pop('order', None)
        limit=extra.pop('limit', None)
        offset=extra.pop('offset', None)
        conn=self.getDBI()
        converter=conn.getConverter()
        wheresql, wherevals=self._processWhere(conn, whereArgs, extra, converter=converter)
        sql, vals = self._joinTableSQL(conn,
                                       thisAttrNames,
                                       pivotTable,
                                       thisSideColumns,
                                       thatSideColumns,
                                       thatObject,
                                       thatAttrNames,
                                       extraTables,
                                       wheresql,
                                       #wherevals,
                                       converter,
                                       order,
                                       limit,
                                       offset)
        results = conn.execute(sql, vals)
        if results:
            return map(thatObject, results)
        return []

    def _joinTableSQL(self,
                      conn,
                      thisAttrNames,
                      pivotTable,
                      thisSideColumns,
                      thatSideColumns,
                      thatObject,
                      thatAttrNames,
                      extraTables,
                      wheresql,
                      #wherevals,
                      converter,
                      order,
                      limit,
                      offset):
        """SQL generating function for joinTable"""
        if extraTables is None:
            extraTables=[]

        thisAttrNames = _tupleize(thisAttrNames)
        thisSideColumns = _tupleize(thisSideColumns)
        thatSideColumns = _tupleize(thatSideColumns)
        thatAttrNames = _tupleize(thatAttrNames)
        
        if len(thisSideColumns) != len(thisAttrNames):
            raise ValueError, ('thisSideColumns and thisAttrNames must '
                               'contain the same number of elements')
        if len(thatSideColumns) != len(thatAttrNames):
            raise ValueError, ('thatSideColumns and thatAttrNames must '
                               'contain the same number of elements')
        
        sql=[thatObject._baseSelect(True),
             ', ',
             ', '.join([pivotTable]+extraTables),
             ' WHERE ']
        
        joins = []
        #converter=conn.getConverter()
        for attr, col in zip(thisAttrNames, thisSideColumns):
            lit=converter(self[attr])
            joins.append("%s.%s = %s" % (pivotTable, col, lit))
        vals=converter.values
        joins.extend(['%s.%s = %s.%s' % (pivotTable,
                                         col,
                                         thatObject.getTable(),
                                         attr) \
                      for attr, col in zip(thatAttrNames,
                                           thatSideColumns)])
        sql.append(' AND '.join(joins))
        if wheresql:
            sql.append(' AND (%s)' % wheresql)
            ## not needed, wherevals are now in the converter already
            #if wherevals:
            #    vals=vals+wherevals
        if filter(None, (order, limit, offset)):
            sql.append(conn.orderByString(order, limit, offset))                
        return ''.join(sql), vals


def arrayfetch(objs, *args, **fieldData):
    """
    An experimental function that returns several an array of PyDO objects.
    objs is a list of PyDO objects, or (PyDOObj, tableAlias) tuples (may be
    intermingled).  *args are like the arguments passed to getSome().
    
    N.B.  This function is deprecated and will be removed in future.
    """
    order=fieldData.pop('order', None)
    limit=fieldData.pop('limit', None)
    offset=fieldData.pop('offset', None)
    qobjs=[]
    for o in objs:
        if isinstance(o, (tuple, list)) and len(o)==2:
            qobjs.append(o)
        else:
            qobjs.append((o, o.getTable()))
    objs=[x[0] for x in qobjs]
    # connectionAlias must be the same for all objects
    caliases=tuple(frozenset(o.connectionAlias for o in objs))
    if len(caliases)!=1:
        raise ValueError, \
              "objects passed to join must have same connection alias"
    dbi=objs[0].getDBI()
    sql, values=PyDO._processWhere(dbi, args, fieldData)
    allcols=[o.getColumns(a) for o, a in qobjs]
    cols=', '.join(', '.join(a) for a in allcols)
    tables=', '.join(formatTexp(o, a) for o, a in qobjs)
    select=["SELECT %s FROM %s" % (cols, tables)]
    if sql:
        select.append(" WHERE ")
        select.append(sql)
    if filter(None, (order, limit, offset)):
        select.append(dbi.orderByString(order, limit, offset))
    result=dbi.execute(''.join(select), values, True)
    if not result:
        return ()
    ret=[]
    for row in result:
        retrow=[]
        for o, cols in izip(objs, allcols):
            d=dict((_strip_tablename(c), row[c]) for c in cols)
            # if all values are NULL, take that as meaning that this
            # is a full join and the whole object is NULL, and append
            # None
            for v in d.itervalues():
                if v is not None:
                    notnull=True
                    break
            else:
                notnull=False
            if notnull:
                retrow.append(o(**d))
            else:
                retrow.append(None)
        ret.append(tuple(retrow))
    return tuple(ret)
            

__all__=['PyDO']
