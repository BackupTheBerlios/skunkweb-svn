# $Id$
# Time-stamp: <01/09/24 13:39:24 smulloni>

######################################################################## 
#  Copyright (C) 2001 Jocob Smullyan <smulloni@smullyan.org>
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
a pleasantly minimal XML-to-Python object translator.
XMLElement can also be used to build XML documents.
The parser requires expat, but XMLElement does not.
Based on the Java xml parser (org.skunk.minixml)
used for SkunkDAV (http://skunkdav.sf.net/).
"""

try:
    import xml.parsers.expat as expat
    
    class ExpatParser:
        """
        takes an input xml string and produces a corresponding XMLElement (deposited in the 'document' attribute).
        Currently ignores comments, CDATA, processing instructions, etc.
        """
        def __init__(self):
            self.__parser=expat.ParserCreate()
            self.__parser.StartElementHandler=self.start
            self.__parser.EndElementHandler=self.end
            self.__parser.CharacterDataHandler=self.data
            self.__stack=[]
            self.document=None
            
        def start(self, tag, attrs):
            elem=makeElement(tag)
            elem.OPEN=1
            if not self.document:
                self.document=elem
            for k, v in attrs.items():
                elem.setAttribute(k, v)
            self.__stack.append(elem)
            
        def data(self, data):
            self.__stack.append(data)
            
        def end(self, tag):
            # find matching tag
            i=-1
            stackLen=len(self.__stack)
            while stackLen+i >= 0:
                pindex=i
                p=self.__stack[i]
                if isinstance(p, XMLElement) and hasattr(p, 'OPEN'):
                    # found element
                    popped=self.__stack[pindex+1:]
                    map (lambda x, y=p: y.addChild(x), popped)
                    delattr(p, 'OPEN')
                    self.__stack=self.__stack[:pindex+1]
                    break
                else:
                    i-=1
                
        def parse(self, data):
            self.__parser.Parse(data, 0)

except ImportError:
    pass
            
XMLNS_ATTR='xmlns'

def makeElement(fullElementName):
    colonIndex=fullElementName.find(':')
    if colonIndex==-1:
        return XMLElement(fullElementName)
    else:
        return XMLElement(fullElementName[colonIndex+1:],
                          fullElementName[:colonIndex])

class XMLElement:

    def __init__(self, name, namespaceCode=None, namespace=None):
        self.name=name
        self.namespaceCode=namespaceCode
        self.__children=[]
        self.__attributes={}
        self.__namespaces={}
        self.__defaultNamespace=''
        if namespace:
            self.setAttribute('%s:%s' % (XMLNS_ATTR, namespaceCode), namespace)
        self.__parent=None

    def __str__(self):
        buff=['<']
        if self.namespaceCode:
            buff.append('%s:' % self.namespaceCode)
        buff.append(self.name)
        for attr, val in self.__attributes.items():
            buff.append(' %s="%s"' % (attr, val))
        if len(self.__children):
            buff.append('>')
            buff.extend(map(str, self.__children))
            buff.append('</')
            if (self.namespaceCode):
                buff.append('%s:' % self.namespaceCode)
            buff.append('%s>' % self.name)
        else:
            buff.append('/>')
        return ''.join(buff)
            
    def getAttribute(self, name):
        if self.__attributes.has_key(name):
            return self.__attributes[name]
        raise KeyError, name

    def setAttribute(self, name, value):
        if name.startswith(XMLNS_ATTR):
            colindex=name.find(':')
            if colindex==-1:
                self.__defaultNamespace=value
            else:
                self.setNamespace(value, name[colindex+1:])
        self.__attributes[name]=value

    def getChildren(self):
        return self.__children[:]

    def addChild(self, child):
        if isinstance(child, XMLElement):
            child.__parent=self
        self.__children.append(child)

    def getNamespace(self, namespaceCode=None):
        if not namespaceCode:
            namespaceCode=self.namespaceCode
        ns=self.__namespaces.get(namespaceCode)
        if not ns and self.__parent!=None:
            ns=self.__parent.getNamespace(namespaceCode)
        return ns

    def getDefaultNamespace(self):
        if (not self.__defaultNamespace) and self.__parent:
            return self.__parent.getDefaultNamespace()
        return self.__defaultNamespace

    def setDefaultNamespace(self, ns):
        self.__defaultNamespace=ns

    def setNamespace(self, namespace, namespaceCode):
        self.__namespaces[namespaceCode]=namespace
        self.namespaceCode=namespaceCode

    def getChild(self, name, namespace=None, index=0):
        i=-1
        for kid in self.__children:
            if kid.name==name and (namespace==None \
                                   or namespace==kid.getNamespace()):
                i+=1
                if i==index:
                    return kid
        return None

########################################################################
# $Log$
# Revision 1.1.2.1  2001/09/27 03:36:07  smulloni
# new pylibs, work on PyDO, code cleanup.
#
########################################################################
        
        

    
            
    
