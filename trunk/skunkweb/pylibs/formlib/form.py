######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#  
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#  
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#  
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111, USA.
########################################################################

from containers import FieldContainer

__all__=['UNDEF', 'Field', 'DomainField', 'Form']

UNDEF=object()

class Field(object):
    def __init__(self,
                 name,
                 description,
                 default=None,
                 multiple=0):
        self.name=name
        self.description=description
        self.__multiple=multiple
        if default==None:
            self.clearDefault()
        else:
            self._set_default(default)
        self.clearValue()

    def _get_default(self):
        return self.__default

    def _set_default(self, default):
        self.checkValue(default)
        self.__default=default

    def clearDefault(self):
        self.__default=None

    default=property(_get_default, _set_default)
        
    def _get_value(self):
        if self.__value is not UNDEF:
            return self.__value
        else:
            return self.default

    def _set_value(self, value):
        self.checkValue(value)
        self.__value=value

    def clearValue(self):
        self.__value=UNDEF

    value=property(_get_value, _set_value)
    
    def _get_multiple(self):
        return self.__multiple

    multiple=property(_get_multiple)

    def checkValue(self, value):
        isseq=isinstance(value, list) or isinstance(value, tuple)
        if self.multiple and not isseq:
            raise ValueError, "value must be a sequence for this field"
        elif isseq and not self.multiple:
            raise ValueError, "value cannot be a sequence for this field"

    def validate(self, form=None):
        pass

class DomainField(Field):
    """
    a variety of field in which the
    the possible values of the field consist
    of an enumeration or menu. 
    """
    def __init__(self,
                 name,
                 domain,
                 description,
                 default=None,
                 multiple=0):
        self.__domain=domain
        Field.__init__(self, name, description, default, multiple)
        
    def _get_domain(self):
        return self.__domain

    def _set_domain(self, domain):
        if self.default is not None and not self.in_domain(self.default, domain):
            raise ValueError, \
                  "pre-existing default conflicts with new domain; "\
                  "clear the default before setting domain"
        self.__domain=domain

    domain=property(_get_domain, _set_domain)

    def in_domain(self, value, domain=None):
        if not domain:
            domain=self.domain
        if value in domain:
            return 1
        if self.multiple and \
               (isinstance(value, list) or isinstance(value, tuple)):
            return reduce(lambda x, y: x and y,
                          [i in domain for i in value])
        return 0

    def checkValue(self, value):
        """
        determines whether the value is permissible for the field.
        This is not meant to perform validation of user input,
        but to prevent programmatic errors.
        """
        Field.checkValue(self, value)
        if not self.in_domain(value):
            raise ValueError, "value not present in domain"
           

class Form(object):
    def __init__(self,
                 name=None,
                 method='POST',
                 action="",
                 enctype=None,
                 fields=None,
                 validators=None):
        self.name=name
        self.method=method
        self.action=action
        self.enctype=enctype
        self.fields=FieldContainer(fields or [],
                                   fieldmapper=lambda x: x.name,
                                   storelists=0)
        self.validators=validators or []
        self.submitted=None

    def getData(self):
        d={}
        for k, v in self.fields.iteritems():
            d[k]=v.value
        return d

    def setData(self, data):
        for k, v in data.iteritems():
            f=self.fields.get(k)
            if f:
                f.value=v

    def reset(self):
        for f in self.fields:
            f.clearValue()

    def validate(self):
        errors={}
        for l in (self.fields, self.validators):
            for v in l:
                e=v.validate(self)
                if e:
                    errors.update(e)
        return errors





    
        
        
        
