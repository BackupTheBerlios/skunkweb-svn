######################################################################## 
#  Copyright (C) 2003 Jacob Smullyan <smulloni@smullyan.org>,
#                     Drew Csillag <drew_csillag@yahoo.com>
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

"""
viewable form and field implementations that delegate the actual
rendering of forms and fields to AE components.
"""

from AE.Component import callComponent, DT_REGULAR, NO
from form import Form
from views import ViewableField, ViewableDomainField, ViewableForm, Viewable

class ComponentViewableMixin(object):
    def __init__(self,
                 component,
                 cache=NO):
        self.component=component
        self.cache=cache

    def getView(self):
        return callComponent(self.component,
                             argDict={'model' : self},
                             compType=DT_REGULAR,
                             cache=self.cache)
    
                                      
                            

class ComponentViewableField(ComponentViewableMixin, ViewableField):
    def __init__(self,
                 name,
                 component,
                 cache=NO,
                 description=None,
                 default=None,
                 required=0,
                 multiple=0,
                 setable=1,
                 **view_attrs):
        ViewableField.__init__(self,
                               name,
                               description,
                               default,
                               required,
                               multiple,
                               setable,
                               **view_attrs)
        ComponentViewableMixin.__init__(self,
                                        component,
                                        cache)
        
class ComponentViewableDomainField(ComponentViewableMixin, ViewableDomainField):
    def __init__(self,
                 name,
                 domain,
                 component,
                 cache=NO,
                 description=None,
                 default=None,
                 required=0,
                 multiple=0,
                 setable=1,
                 lenient=0,
                 **view_attrs):
        ViewableDomainField.__init__(self,
                                     name,
                                     domain,
                                     description,
                                     default,
                                     required,
                                     multiple,
                                     setable,
                                     lenient,
                                     **view_attrs)
        ComponentViewableField.__init__(self,
                                        component,
                                        cache)
        
class ComponentViewableForm(ComponentViewableMixin, Viewable, Form):
    def __init__(self,
                 component,
                 cache=NO,
                 name=None,
                 method=None,
                 action=None,
                 enctype=None,
                 fields=None,
                 validators=None,
                 processors=None,
                 **view_attrs):
        ComponentViewableMixin.__init__(self,
                                        component,
                                        cache)
        Viewable.__init__(self,
                          **view_attrs)
        Form.__init__(self,
                      name,
                      method,
                      action,
                      enctype,
                      fields,
                      validators,
                      processors)


        
        
__all__=['ComponentViewableField',
         'ComponentViewableDomainField',
         'ComponentViewableForm']