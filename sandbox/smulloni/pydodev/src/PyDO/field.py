

class Field(object):
    """represents a column in a database table."""

    __slots__=('attrname', 'dbtype', 'dbname', 'attrs')
    
    def __init__(self, dbname, dbtype, attrname=None, attrs=None):
        self.dbname=dbname
        self.dbtype=dbtype
        if attrname is None:
            self.attrname=dbname
        else:
            self.attrname=attrname
        self.attrs=attrs

    def __repr__(self):
        return "<%s instance \"%s\" at %x>" % \
               (self.__class__.__name__,
                self.dbname,
                id(self))









        
