
"""
A lexer for STML.

kinds of tokens:

   t_TEXT -- the undifferentiated stuff outside of tags.
   t_START_TAG -- the "<:" characters that start a tag
   t_END_TAG -- the ":>" characters that end a tag
   t_TAGNAME -- the first word in a tag (a bare unquoted word)
   t_TAGWORD -- other bare (unquoted) words in tags
   t_EQUALS -- equals sign in tags, between attributes and values
   t_EXPR -- Python expressions in tags (between backticks)
   t_QUOTED STRING -- string literals in tags

also two types that are not actually returned by the lexer:

      t_COMMENT -- comments
      t_PI -- processing instructions

kinds of states:
   s_TEXT (expect t_TEXT, t_COMMENT, EOF, or t_START_TAG)
   s_START_TAG (expect t_TAGNAME)
   s_IN_TAG (expect t_TAGWORD, t_EXPR, t_END_TAG, t_QUOTED_STRING)
   s_TAGATTR (expect t_TAGWORD, t_EXPR, t_END_TAG, t_QUOTED_STRING, t_EQUALS)
   s_TAGVAL (expect t_TAGWORD, t_EXPR, t_QUOTED_STRING)

whitespace handling comes in two flavors, controlled by the processing
instructions <:?pre on?:> and <:?pre off?:>.

in addition, while not necessary, IN_SINGLE_QUOTE, IN_DOUBLE_QUOTE,
and IN_EXPR may be used as conveniences (although this implementation
currently does not).

The actual tokens returned may need to be enriched, but I'm starting out
by returning minimal information (the token type and the text of the token,
if any).  Offset, line number, etc. can be added later.

TODO

* make lexical errors better (should print more stuff)
* treatment of lineno isn't ideal.

"""

import re
from string import whitespace
from skunk.templating.stml.exceptions import *

# states
s_TEXT='s_TEXT'
s_START_TAG='s_START_TAG'
s_IN_TAG='s_IN_TAG'
s_TAGATTR='s_TAGATTR'
s_TAGVAL='s_TAGVAL'

# tokens
t_TEXT='t_TEXT'
t_START_TAG='t_START_TAG'
t_END_TAG='t_END_TAG'
t_TAGNAME='t_TAGNAME'
t_TAGWORD='t_TAGWORD'
t_EQUALS='t_EQUALS'
t_EXPR='t_EXPR'
t_QUOTED_STRING='t_QUOTED_STRING'

# currently not used
#t_COMMENT='t_COMMENT'
#t_PI='t_PI'

# regexes to detect tokens or other patterns

# I allow a colon in the middle of the word, in case someone wants to use
# xml-namespace-style tag names.  
p_TAGNAME=re.compile('(?:[^\\s="\'`:<>]+:[^\\s="\'`:<>]+)|[^\\s="\'`:<>]+')
p_TAGWORD=p_TAGNAME
p_EXPR=re.compile('`(.*?)`', re.S)
p_QUOTED_STRING=re.compile('\'(.*?)\'|"(.*?)"')
p_START_TAG=re.compile('<:')
p_END_TAG=re.compile(':>')
p_NONWS=re.compile(r'[^\s]')
p_PI=re.compile(r'(.*?)\?:>')
p_PRE_PI=re.compile(r'\s*pre\s+(on|off)\s*')

# whether to preserve formatting by default
DEFAULT_PRE=0

def _lineno(offset, linebrks):
    """
    internal function to determine the line number
    of offset given an array of indices of line returns
    """
    i=0
    for i, n in enumerate(linebrks):
        if offset<n:
            return i
    return i+1

class STMLToken(object):
    __slots__=('tokenType',
               'offset',
               'lineno',
               'text')
    
    def __init__(self,
                 tokenType,
                 offset,
                 lineno,
                 text=None):
        self.tokenType=tokenType
        self.offset=offset
        self.lineno=lineno
        self.text=text

    def __len__(self):
        if self.text:
            return len(self.text)
        return 0

    def __repr__(self):
        return "<STMLToken %s at %d, line %d: \"%s\">" % (self.tokenType,
                                                          self.offset,
                                                          self.lineno,
                                                          self.text)

    def __str__(self):
        return self.text or ""
        

def lex(s, pre=False):
    """
    tokenizes the STML string s, returning a generator which yields successive tokens.
    """
    state=s_TEXT
    offset=0
    l=len(s)
    
    # gets the indices of all line breaks all at once in once pass,
    # for subsequent determination of line numbers from offset.  This
    # saves me from having to worry about line breaks in subsequent
    # lexing, which simplifies some things, at the cost of an
    # additional scan of the string, and retaining the indices in
    # memory.
    getlineno=lambda x: _lineno(x, [i for i, x in enumerate(s) if x=='\n'])

    # convenience function that advances through insignificant
    # whitespace, used several times within tags
    def _advanceWS():
        m=p_NONWS.search(s, offset)
        if m:
            return m.start()
        else:
            raise LexicalError('unfinished tag',
                               offset,
                               getlineno(offset))
    
    while offset < l:
        if state==s_TEXT:
            # t_PI
            if s[offset:offset+3]=='<:?':
                m=p_PI.match(s, offset+3)
                if not m:
                    raise LexicalError("unfinished processing instruction",
                                       offset,
                                       getlineno(offset))
                e=m.end()
                m=p_PRE_PI.match(m.group(1))
                if not m:
                    raise LexicalError("invalid processing instruction",
                                       offset,
                                       getlineno(offset))
                pre= m.group(1)=='on'
                offset=e
                continue
            
            # t_COMMENT
            if s[offset:offset+3]=='<:*':
                try:
                    i=s.index('*:>', offset+3)
                except ValueError:
                    raise LexicalError("unfinished comment",
                                       offset,
                                       getlineno(offset))
                # state remains s_TEXT
                offset=i+3
                continue
            
            # t_START_TAG
            if p_START_TAG.match(s, offset):
                yield STMLToken(t_START_TAG, offset, getlineno(offset), '<:')
                state=s_START_TAG
                offset+=2
                continue
            # anything else until the next start tag is t_TEXT
            # strip whitespace here depending on the value of pre -- TO BE DONE            
            if not pre:
                try:
                    offset=_advanceWS()
                except LexicalError:
                    offset=l
                    break
            i=s.find('<:', offset)
            if i == -1:
                if not pre:
                    tokstring=s[offset:].strip()
                else:
                    tokstring=s[offset:]
                if tokstring:
                    yield STMLToken(t_TEXT, offset, getlineno(offset), tokstring)
                offset=l
                break
            else:
                if not pre:
                    tokstring=s[offset:i].strip()
                else:
                    tokstring=s[offset:i]
                if tokstring:
                    yield STMLToken(t_TEXT, offset, getlineno(offset), tokstring)
                offset=i
                continue

        elif state==s_START_TAG:

            # match t_TAGNAME, move to s_IN_TAG, or error
            m=p_TAGNAME.match(s, offset)
            if m:
                yield STMLToken(t_TAGNAME, offset, getlineno(offset), m.group())
                offset=m.end()
                state=s_IN_TAG
                continue
            else:
                raise LexicalError("unrecognizable stuff after <:",
                                   offset,
                                   getlineno(offset))
        
        elif state==s_IN_TAG:
            # skip ahead to the first non-whitespace
            # before checking
            offset=_advanceWS()

            # t_END_TAG
            m=p_END_TAG.match(s, offset)
            if m:
                yield STMLToken(t_END_TAG, offset, getlineno(offset), ':>')
                offset=m.end()
                state=s_TEXT
                continue
            
            # t_TAGWORD
            m=p_TAGWORD.match(s, offset)
            if m:
                yield STMLToken(t_TAGWORD, offset, getlineno(offset), m.group())
                offset=m.end()
                state=s_TAGATTR
                continue

            # t_EXPR
            m=p_EXPR.match(s, offset)
            if m:
                yield STMLToken(t_EXPR, offset, getlineno(offset), m.group(1))
                offset=m.end()
                # state remains s_IN_TAG
                continue

            # t_QUOTED_STRING
            m=p_QUOTED_STRING.match(s, offset)
            if m:
                
                yield STMLToken(t_QUOTED_STRING, offset, getlineno(offset),
                                m.group(1) or m.group(2) or "")
                offset=m.end()
                # state remains s_IN_TAG
                continue

            # you don't want to get here
            raise LexicalError("junk in tag",
                               offset,
                               getlineno(offset))
        
        elif state==s_TAGATTR:
            # skip ahead to the first non-whitespace
            # before checking
            offset=_advanceWS()

            # t_EQUALS
            if s[offset]=='=':
                yield STMLToken(t_EQUALS, offset, getlineno(offset), '=')
                offset+=1
                state=s_TAGVAL
                continue

            else:
                state=s_IN_TAG
                continue

        elif state==s_TAGVAL:
            # skip ahead to the first non-whitespace
            # before checking
            offset=_advanceWS()
            
            # t_TAGWORD
            m=p_TAGWORD.match(s, offset)
            if m:
                yield STMLToken(t_TAGWORD, offset, getlineno(offset), m.group())
                offset=m.end()
                state=s_IN_TAG
                continue

            # t_EXPR
            m=p_EXPR.match(s, offset)
            if m:
                yield STMLToken(t_EXPR, offset, getlineno(offset), m.group(1))
                offset=m.end()
                state=s_IN_TAG
                continue

            # t_QUOTED_STRING
            m=p_QUOTED_STRING.match(s, offset)
            if m:
                yield STMLToken(t_QUOTED_STRING, offset, getlineno(offset),
                                m.group(1) or m.group(2) or "")
                offset=m.end()
                state=s_IN_TAG
                continue
            
            raise LexicalError("unfinished tag",
                               offset,
                               getlineno(offset))
        raise StopIteration

        
def dump_tokens(s, pre=False):
    """
    tokenizes an STML string and returns all tokens as a list.
    """
    return list(lex(s, pre))

__all__=['lex',
         'dump_tokens',
         'STMLToken',
          't_TEXT',
          't_START_TAG',
          't_END_TAG',
          't_TAGNAME',
          't_TAGWORD',
          't_EQUALS',
          't_EXPR',
          't_QUOTED_STRING']
