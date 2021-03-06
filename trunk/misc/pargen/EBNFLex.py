#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""A lexer for EBNF grammars"""

import string
import re
import types

quotedString = re.compile(r"'([^'\\]|\\'|\\[^'])*?'")
commentRe = re.compile('#.*')
token = re.compile('[A-Za-z_][A-Za-z0-9_]*')
wsre = re.compile(r'\s+')
class Token:
    def __init__(self, ttype, tval):
        self.toktype=ttype
        self.tokval=tval
    def __repr__(self):
        return '<Token %s : "%s">' % (self.toktype, self.tokval)

toklook = (
    ('(', '(', '('),
    (')', ')', ')'),
    ('|', '|', '|'),
    ('*', '*', '*'),
    ('+', '+', '+'),
    ('[', '[', '['),
    (']', ']', ']'),
    (':', 'COLON', ':'),
    (wsre, 'COMMENT', lambda x:''),
    (commentRe, 'COMMENT', lambda x:''),
    (quotedString, 'TOKEN', lambda x: x.group(1)),
    (token, 'TOKEN', lambda x: x.group()),
    )

def lexExp(text):
    """lex the text and return a list of tokens"""
    toks=[]
    offset=0
    while offset < len(text):
        chunk=text[offset:]
        for i in toklook:
            lookPart = i[0]
            if type(lookPart) == type(''): # a literal thing
                if chunk[:len(lookPart)] == lookPart:
                    offset = offset + len(lookPart)
                    toks.append(Token(i[1], i[2]))
                    break 
            else: # a regex
                #print 'checking %s against %s' % (chunk[:10], i[0].pattern)
                lre=i[0]
                m=lre.match(chunk)
                #print 'm =', m
                if m:
                    if len(i)==1:
                        offset=offset+m.end()
                        break
                    elif type(i[1])==types.LambdaType:
                        tokname=i[1](m)
                    else:
                        tokname=i[1]
                    toks.append(Token(tokname, i[2](m)))
                    offset=offset+m.end()
                    break
        else:
            raise 'LexicalError', 'Invalid thing in query >%s<' % chunk[:10]
    return filter(lambda x:x.toktype != 'COMMENT', toks)

