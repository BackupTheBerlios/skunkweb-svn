import keyword
import warnings


class Field(object):
    """represents a column in a database table."""

    __slots__=('name', 'sequence', 'unique', 'dbtype', 'nullable')
    
    def __init__(self,
                 name,
                 sequence=False,
                 unique=False,
                 dbtype=None,
                 nullable=None):
        self.name=name
        if name in keyword.kwlist:
            warnings.warn('field name "%s" is a Python keyword!' % name)        
        self.sequence=sequence
        self.unique=unique
        self.dbtype=dbtype
        self.nullable=nullable


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

class Sequence(Field):
    """like a Field, except that sequence defaults to True, and the field must be unique.
    If a sequence name needs to be specified, pass it through the "sequence" parameter.
    
    If for some reason you want a non-unique sequence, whatever that is, use the Field class
    directly
    """
    def __init__(self,
                 name,
                 sequence=None,
                 dbtype=None,
                 nullable=None):
        if sequence is None:
            sequence=True
        super(Sequence, self).__init__(name,
                                       sequence,
                                       True,
                                       dbtype,
                                       nullable)

class Unique(Field):
    """like a Field, except that it must be unique and isn't a sequence (use Sequence for that)"""
    def __init__(self,
                 name,
                 dbtype=None,
                 nullable=None):
        super(Unique, self).__init__(name,
                                     False,
                                     True,
                                     dbtype,
                                     nullable)


__all__=['Field', 'Sequence', 'Unique']







        
