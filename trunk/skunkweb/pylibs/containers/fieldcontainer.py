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

try:
    list
except NameError:
    import UserList.UserList as list

class FieldContainer(list):
    """
    a list with a read-only dict interface.
    The keys of the dict are determined by a
    function supplied by the user at construction-time.
    If the constructor argument storelists is true,
    the dict interface returns for each key a list of
    items with that key, or raises a KeyError; otherwise,
    it returns a single item for each key and raises a
    ValueError if you try to add another item with the
    same key to the list. 

    While the list is fully mutable, and changes to
    the list are reflected by the dict interface,
    it wouldn't make sense to permit dict-style mutation,
    i.e., fc['fieldkey']=fieldlist, because it would
    not be order-preserving; the purpose of this container
    is to maintain order of the items contained while
    also grouping them by key for reference.

    Example:

    >> class foo:
    >>    def __init__(self, name):
    >>       self.name=name
    
    >> fc=FieldContainer(map(foo, 'this is a dormouse is this not'.split()),
                         lambda x: x.name)
    >>> fc.keys()
    ['this', 'a', 'is', 'not', 'dormouse']
    >>> fc['is']
    [<__main__.foo instance at 0x817fb0c>, <__main__.foo instance at 0x815a34c>]
    >>> fc['dormouse']
    [<__main__.foo instance at 0x817fb5c>]
    >>> [x.name for x in fc]
    ['this', 'is', 'a', 'dormouse', 'is', 'this', 'not']
    
    """

    __slots__=['_FieldContainer__d', 'fieldmapper', 'storelists']

    def __new__(self, seq=None, fieldmapper=None, storelists=1):
        return list.__new__(self, seq)

    def __init__(self, seq=None, fieldmapper=None, storelists=1):
        list.__init__(self, seq or [])
        if fieldmapper is None:
            self.fieldmapper=lambda x: x
        else:
            self.fieldmapper=fieldmapper
        self.__d={}
        self.storelists=storelists
        if seq:
            for s in seq:
                self.__register_field(s)

    def __register_field(self, field):
        k=self.fieldmapper(field)
        if self.storelists:
            self.__d.setdefault(k, [])
            self.__d[k].append(field)
        else:
            if self.__d.has_key(k):
                raise ValueError, "cannot add a duplicate key"
            self.__d[k]=field

    def __unregister_field(self, field):
        k=self.fieldmapper(field)
        if self.storelists:
            flist=self.__d[k]
            flist.remove(field)
            if not flist:
                del self.__d[k]
        else:
            del self.__d[k]

    def __getitem__(self, key):
        if isinstance(key, int):
            return list.__getitem__(self, key)
        return self.__d[key]

    def get(self, key, default=None):
        return self.__d.get(key, default)

    def __setitem__(self, index, item):
        if not isinstance(index, int):
            raise TypeError, "cannot set items by key, only by index"
        try:
            x=list.__getitem__(self, index)
        except IndexError:
            raise IndexError, "index out of range"
        self.__unregister_field(x)
        self.__register_field(item)
        list.__setitem__(self, index, item)

    def __delitem__(self, index):
        try:
            x=list.__getitem__(self, index)
        except IndexError:
            raise IndexError, "index out of range"
        self.__unregister_field(x)
        list.__delitem__(self, index)

    def __getslice__(self, i, j):
        x=list.__getslice__(self, i, j)
        return self.__class__(x, self.fieldmapper, self.storelists)

    def __setslice__(self, i, j, seq):
        old=list.__getslice__(self, i, j)
        for f in old:
            self.__unregister_field(f)
        for f in seq:
            self.__register_field(f)
        list.__setslice__(self, i, j, seq)

    def insert(self, index, object):
        self.__register_field(object)
        list.insert(self, index, object)

    def append(self, object):
        self.__register_field(object)
        list.append(self, object)

    def extend(self, alist):
        for x in alist:
            self.__register_field(x)
        list.extend(self, alist)

    def remove(self, item):
        list.remove(self, item)
        self.__unregister_field(item)

    def has_key(self, key):
        return self.__d.has_key(key)

    def keys(self):
        return self.__d.keys()

    def items(self):
        return self.__d.items()

    def values(self):
        return self.__d.values()
    
    def iterkeys(self):
        return self.__d.iterkeys()

    def iteritems(self):
        return self.__d.iteritems()

    def itervalues(self):
        return self.__d.itervalues()

    def to_dict(self):
        return self.__d.copy()
