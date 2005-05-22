"""
produces a parse tree from the output of lexer.lex().
"""
from skunk.templating.stml.lexer import *
from skunk.templating.stml.signature import Signature
from skunk.templating.stml.exceptions import ParseError

class Expr(object):
    """
    wrapper for expressions.
    """
    __slots__=['text']
    
    def __init__(self, text):
        self.text=text

    def __repr__(self):
        return self.text
        

class Node(object):
    """
    
    base class for STML tag nodes; also for RootNode, even though it
    has no tag.

    Class attributes, which should be shadowed by sub-classes:
    
    signature
       the tag signature.
       
    isBlock
       whether the tag is a block tag or not.
       
    localTagDict
       if this is a block tag, a dictionary of tags that can occur
       within the block in addition to whatever is globally available

    modules
       modules that code generated by this tag may need; they will be
       imported into the hidden namespace (__h).  Either an actual
       module, a module name, or a tuple (module_or_module_name,
       module_alias) can appear in this list.

    tagName
       the name of the tag.
       
    """
    
    signature=Signature(())
    isBlock=False
    localTagDict={}
    modules=[]
    tagName=None
    
    __slots__=['globalTagDict',
               'children',
               'args',
               'kwargs',
               '_parsed_args',
               '_token',
               'prefix',
               'root',
               'parent']
    
    def __init__(self,
                 globalTagDict=None,
                 parent=None,
                 root=None,
                 prefix=None):
        self.globalTagDict=globalTagDict or {}
        self.children=[]
        self.args=[]
        self.kwargs={}
        self._token=None
        self.prefix=prefix
        self.root=root
        self.parent=parent

    def _init_temporary_namespace(cls, nsObj):
        """
        class method usable by subclasses if they need to initialize
        the temporary namespace
        """
        pass
    _init_temporary_namespace=classmethod(_init_temporary_namespace)
        

    def parse(self, lexer):
        """
        builds the node tree from the lexer.
        """
        self._parse_tag(lexer)
        self._parsed_args=self.signature.resolve_arguments(self.args, self.kwargs)
        if self.isBlock:
            self._parse_block(lexer)

    def _parse_tag(self, lexer):
        # you enter this when the tagname has already been identified
        curarg=None
        state=None
        while 1:
            try:
                self._token=token=lexer.next()
            except StopIteration:
                if state is None:
                    break
                else:
                    # the lexer must be broken, it should have
                    # raise a LexicalError earlier
                    raise ParseError("incomplete input, hit EOF in tag")
            else:
                if state is None:
                    state="intag"
                                     
            tokenType=token.tokenType
            if tokenType==t_TAGNAME:
                self.handle_tagname(token.text)
                # this doesn't happen here
                assert False
                continue
            elif tokenType==t_EQUALS:

                if curarg is None:
                    self.handle_error("unexpected equals sign")
                state="expectval"
                continue
            elif tokenType==t_EXPR:
                if state=='expectval':
                    if curarg in self.kwargs:
                        self.handle_error("duplicate keyword argument")
                    self.kwargs[curarg]=Expr(token.text)
                    curarg=None
                    state='intag'
                else:
                    if curarg is not None:
                        self.args.append(curarg)
                    curarg=Expr(token.text)

            elif tokenType==t_TAGWORD or tokenType==t_QUOTED_STRING:
                if state=='expectval':
                    if curarg in self.kwargs:
                        self.handle_error("duplicate keyword argument")
                    self.kwargs[curarg]=Expr(repr(token.text))
                    curarg=None
                    state='intag'
                else:
                    if curarg is not None:
                        self.args.append(curarg)
                    curarg=token.text

            elif tokenType==t_END_TAG:
                if curarg is not None:
                    self.args.append(curarg)
                break
            else:
                self.handle_error("unexpected token", token)

    def handle_eof_in_block(self):
        """
        if an EOF occurs inside a block, this handles
        it, by default, raising an error.
        """
        self.handle_error("hit EOF, expected close tag")

    def _parse_block(self, lexer):
        while 1:
            try:
                self._token=token=lexer.next()
            except StopIteration:
                if self.isBlock:
                    return self.handle_eof_in_block()
                else:
                    break
            tokenType=token.tokenType
            if tokenType==t_TEXT:
                self.handle_text(token)
            elif tokenType==t_START_TAG:
                # ignore, we'll handle this
                # for t_TAGNAME
                continue
            elif tokenType==t_TAGNAME:
                closed=self.handle_tag(token, lexer)
                if closed:
                    break
            else:
                self.handle_error("unexpected token", token)


    def _find_tag(self, token, tagName, prefix):
        """
        look up the tag in the global, local, and component tag
        dictionaries, then in the inherited local tag dictionaries.
        """
        fulltag=token.text
        try:
            return self.globalTagDict[fulltag]
        except KeyError:
            pass
        if prefix==self.prefix:
            try:
                return  self.localTagDict[tagName]
            except KeyError:
                pass
        
        try:
            return self.root._extraTagDict[fulltag]
        except KeyError:
            pass

        p=self.parent
        while p:
            if p.prefix==prefix:
                try:
                    return p.localTagDict[tagName]
                except KeyError:
                    pass
            p=p.parent
        
        self.handle_error("tag not found: %s" % fulltag, token)

    def handle_text(self, token):
        self.children.append(token.text)

    def _split_tagname(self, tagname):
        if ':' in tagname:
            return tagname.split(':', 1)
        else:
            return None, tagname
        

    def handle_tag(self, token, lexer):
        """
        parses any tag in the block, creating child nodes as necessary
        """
        if token.text.startswith('/'):
            return self.handle_close_tag(token, lexer)
        else:
            prefix, tagname=self._split_tagname(token.text)        
            tagNodeClass=self._find_tag(token, tagname, prefix)
            if tagNodeClass.isBlock:
                node=tagNodeClass(self.globalTagDict,
                                  prefix=prefix,
                                  parent=self,
                                  root=self.root)
            else:
                node=tagNodeClass(parent=self,
                                  prefix=prefix,
                                  root=self.root)
            self.children.append(node)
            node.parse(lexer)
            return False

    def handle_close_tag(self, token, lexer):
        """
        handler for a close tag
        """
        prefix, tag=self._split_tagname(token.text[1:])
        if self.tagName==tag and self.prefix==prefix:
            self._token=t=lexer.next()
            if t.tokenType==t_END_TAG:
                return True
            else:
                self.handle_error("malformed tag")
        # if we get here
        self.handle_error('close tag not expected in this context')
        
            
    def handle_error(self, msg, token=None):
        """
        raises a ParseError
        """
        if token is None:
            token=self._token
            if token is None:
                raise ParseError(msg, 0, 0)
        raise ParseError("%s: %s (%s)" % (msg,
                                          token.text,
                                          token.tokenType),
                         token.offset,
                         token.lineno)

class RootNode(Node):
    """
    a spurious, tagless node that includes an entire template.
    It has an extra attribute, '_extraTagDict', for component-local
    tag libraries.
    """
    isBlock=True
    __slots__=['_extraTagDict']
    
    def __init__(self,
                 globalTagDict=None):
        Node.__init__(self,
                      globalTagDict,
                      root=self)
        self._extraTagDict={}

    def _parse_tag(self, lexer):
        # no tag, hence no parsing
        pass

    def handle_eof_in_block(self):
        pass

    def useTagLibrary(self, taglib, prefix=None):
        """
        import a tag library for use locally in the document.  If prefix
        is supplied, it should be a string, and tags should be written
        <:prefix:tagname:>.
        """
        if prefix is not None:
            taglib=dict([('%s:%s' % (prefix, k), v) for k, v in taglib.items()])
        self._extraTagDict.update(taglib)

        


def parse(s, tagVocabulary):
    """
    given a string containing STML and a tag vocabulary, returns a
    parsed RootNode.
    """
    n=RootNode(globalTagDict=tagVocabulary)
    n.parse(lex(s))
    return n

__all__=['Node', 'RootNode', 'Expr', 'parse']
