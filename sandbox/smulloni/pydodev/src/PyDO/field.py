

class Field(object):
    """represents a column in a database table."""

    __slots__=('name', 'dbtype', 'dbname', 'attrs')
    
    def __init__(self, name, dbtype, dbname=None, attrs=None):
        self.name=name
        self.dbtype=dbtype
        if dbname is None:
            self.dbname=name
        self.attrs=attrs

    def __repr__(self):
        return "<%s instance \"%s\" at %x>" % \
               (self.__class__.__name__,
                self.name,
                id(self))









        
