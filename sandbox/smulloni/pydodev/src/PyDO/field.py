import keyword
import warnings

class Field(object):
    """represents a column in a database table."""

    __slots__=('dbname', 'dbtype', 'pyname', 'attrs')
    
    def __init__(self, dbname, dbtype, attrs=None):
        self.dbname=dbname
        self.dbtype=dbtype
        if dbname in keyword.kwlist:
            warnings.warn(('field name "%s" is a Python keyword'\
                          ', in code use %s_!') % (dbname, dbname))
            self.pyname=dbname+'_'
        else:
            self.pyname=dbname
        self.attrs=attrs

    def __get__(self, obj, type_):
        """descriptor method"""
        return obj[self.pyname]
    
    def __set__(self, obj, value):
        """descriptor method"""
        return obj.update[{self.pyname: value}]

    def __str__(self):
        return self.pyname

    def __repr__(self):
        return "<%s instance \"%s\" at %x>" % \
               (self.__class__.__name__,
                self.pyname,
                id(self))


class _fieldset(object):
    __slots__=('pynames', 'dbnames', 'fields', 'typedict')
    
    def __getstate__(self):
        return (self.pynames, self.dbnames, self.fields, self.typedict)

    def __setstate__(self, state):
        (self.pynames, self.dbnames, self.fields, self.typedict)=state
        
    def __init__(self, iterable=None):
        self.pynames={}
        self.dbnames={}
        self.fields=[]
        self.typedict={}
        if iterable:
            self.update(iterable)

    def __iter__(self):
        return self.fields.__iter__()

    def register(self, field):
        self.pynames[field.pyname]=field
        self.dbnames[field.dbname]=field
        self.typedict[field.dbname]=field.dbtype
        self.fields.append(field)

    def unregister(self.field):
        del self.pynames[field.pyname]
        del self.dbnames[field.dbname]
        del.self.typedict[field.dbname]
        self.fields.remove(field)

    def update(self, fieldlist):
        for x in fieldlist:
            self.register(x)

__all__=['Field']







        
