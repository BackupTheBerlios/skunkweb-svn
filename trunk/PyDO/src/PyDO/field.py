import keyword
import warnings


class Field(object):
    """represents a column in a database table."""

    __slots__=('name', 'dbtype', 'attrs')
    
    def __init__(self, name, dbtype=None, attrs=None):
        self.name=name
        self.dbtype=dbtype
        if name in keyword.kwlist:
            warnings.warn('field name "%s" is a Python keyword!' % name)
        self.attrs=attrs

    def __get__(self, obj, type_):
        """descriptor method"""
        return obj[self.name]
    
    def __set__(self, obj, value):
        """descriptor method"""
        return obj.update({self.name: value})

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s instance \"%s\" at %x>" % \
               (self.__class__.__name__,
                self.name,
                id(self))


__all__=['Field']







        
