#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import string
import sys
import re
import ErrorHandler
import SkunkExcept
from DTExcept import DTLexicalError
import StringIO

#regex for a quoted string (no backslash escaping)
quotedStr="('(.*?)' | \"(.*?)\" | `(.*?)`)"

#plain thing
plain='[^\s="\'`]+'

plainre=re.compile(plain)

#regex for parsing contents of a tag
tagContents='''(
     (?P<plain> %(plain)s ) (?=($|\s)) | 
     (?P<plaineq> %(plain)s ) \s*
               = \s* (?P<plaineqval> %(plain)s ) (?=($|\s)) |
     (?P<plaineqq> %(plain)s ) \s*
               = \s* (?P<plaineqqval> %(quotedStr)s ) (?=($|\s)) |
     (?P<quotonly> %(quotedStr)s (?=($|\s))) |
     (?P<whitespace> \s)
         )''' % {'plain': plain,
                 'quotedStr': quotedStr
                 }
tagContentsRe=re.compile(tagContents, re.VERBOSE | re.DOTALL)
PLAIN='plain'
PLAINEQ='plaineq'
PLAINEQVAL='plaineqval'
PLAINEQQ='plaineqq'
PLAINEQQVAL='plaineqqval'
QUOTONLY='quotonly'
WHITESPACE='whitespace'

wsre = re.compile(r'\s+')
def dequote(s):
    if s[0]==s[-1]=='"':
        return s[1:-1]
    elif s[0]==s[-1]=="'":
        return s[1:-1]
    return s

class DTToken:
    def __init__(self, text, name, (start, end, tagname, tup, dict)):
        self.text=text
        self._name=name
        self.start=start
        self.end=end
        self.tagname=tagname
        self.tupargs=tuple(tup)
        self.dictargs=dict

        if self.tagname[0]=='/':
            self.isclose=1
            self.tagname=self.tagname[1:]
        else:
            self.isclose=0

    def filename(self):
        return self._name

    def filelineno(self):
        return "%s:%s" % (self._name, self.getLineno())

    def lineno(self):
        return int(self.getLineno())
    
    def getLineno(self):
        return getLineno(self.text, self.start)

    def tagText(self):
        return self.text[self.start:self.end]

    def __repr__(self):
        tupvals=' '.join(map(repr, self.tupargs))
        if tupvals:
            tupvals=' '+tupvals
        dl=[]
        for k,v in self.dictargs.items():
            dl.append('%s=%s' % (k, repr(v)))
        dictvals=' '.join(dl)
        if dictvals:
            dictvals=' '+dictvals
        close=self.isclose and '/' or ''
        return '<:%s%s%s%s:>' % (close,
                                 self.tagname,
                                 tupvals,
                                 dictvals)

(INIT, GOTLT, PLAINTAGTEXT, SQUOT, BQUOT, DQUOT, GOTCCOL, BACKSLASH,
 BEGINCOMMENTCHECK, INCOMMENT, INCOMMENTSTAR, INCOMMENTSTARCOL) = range(12)
_statenumtostr = {
    INIT:'INIT',
    GOTLT:'GOTLT',
    PLAINTAGTEXT:'PLAINTAGTEXT',
    SQUOT:'SQUOT',
    BQUOT:'BQUOT',
    DQUOT:'DQUOT',
    GOTCCOL:'GOTCCOL',
    BACKSLASH:'BACKSLASH',
    BEGINCOMMENTCHECK:'BEGINCOMMENTCHECK',
    INCOMMENT:'INCOMMENT',
    INCOMMENTSTAR:'INCOMMENTSTAR',
    INCOMMENTSTARCOL:'INCOMMENTSTARCOL',
}

def findTags(text):
    ret = []

    PTTSTATESWITCH = {
        ":": GOTCCOL,
        "'": SQUOT,
        '"': DQUOT,
        "`": BQUOT
        }
    VALID_PTTEXT = (string.letters + string.digits + string.whitespace
                    + '[]_=/\\#.*')
    QUOTE_CLOSE = {
        SQUOT: "'",
        DQUOT: '"',
        BQUOT: '`'
        }
        
    offset = 0
    lentext = len(text)
    state = INIT

    backslash_save_state = 0

    textoffset = 0
    tagoffset = 0
    while offset < lentext:
        c = text[offset]
        if state == INIT:
            if c == '<':
                tagoffset = offset
                state = GOTLT
        elif state == GOTLT:
            if c == ':':
                state = BEGINCOMMENTCHECK
                #put in text token
                ret.append( (textoffset, offset - 1, 0, 
                             text[textoffset:offset - 1]) )
            elif c == '<':
                tagoffset = offset
            else:
                state = INIT
        elif state == BEGINCOMMENTCHECK:
            if c != '*':
                state = PLAINTAGTEXT
                continue
            state = INCOMMENT
        elif state == INCOMMENT:
            if c == '*':
                state = INCOMMENTSTAR
        elif state == INCOMMENTSTAR:
            if c == ':':
                state = INCOMMENTSTARCOL
            else:
                state = INCOMMENT
        elif state == INCOMMENTSTARCOL:
            if c == '>':
                state = INIT
                textoffset=offset+1
            else:
                state = INCOMMENT
        elif state == PLAINTAGTEXT:
            nstate = PTTSTATESWITCH.get(c)
            if nstate:
                state = nstate
            elif c == '\\':
                backslash_save_state = state
                state = BACKSLASH
            elif c not in VALID_PTTEXT:

                if c != '<': #not beginning of next tag?
                    raise DTLexicalError( lineno = getLineno ( text, offset), 
                                    msg = "invalid character |%s| in tag" % c)
                else:
                    raise DTLexicalError( lineno = getLineno ( text, offset ),
                                      msg = "found < in tag" )
        elif state == GOTCCOL:
            if c != ">":
                state=PLAINTAGTEXT
            else:    
                textoffset = offset + 1
                # put in tag token
                ret.append(
                    [tagoffset, offset + 1, 1, text[tagoffset + 2: offset - 1]]
                    )
                state = INIT
            
        elif state in (SQUOT, DQUOT, BQUOT):
            if c == '\\':
                backslash_save_state = state
                state = BACKSLASH

            elif c == QUOTE_CLOSE[state]:
                state = PLAINTAGTEXT

        elif state == BACKSLASH:
            state = backslash_save_state

        offset = offset + 1
    # GOTLT should be an acceptable state for the file
    # to terminate in
    if state != INIT and state != GOTLT:
        md = {PLAINTAGTEXT: "text",
              SQUOT:    "in single quoted area",
              DQUOT:    "in double quoted area",
              BQUOT:    "in expression area",
              GOTCCOL:  "after closing colon",
              BACKSLASH: "after backslash",
	      INCOMMENT: "in comment"
              }
        raise DTLexicalError(msg = "hit end of file %s in tag, beginning of "
                             "tag %s at" % (md.get(state, "[unknown state]"),
                                            text[tagoffset:tagoffset+10]+"..."),
                             lineno = getLineno ( text, tagoffset ))
    else:
        ret.append([textoffset, offset, 0, text[textoffset:offset]])
    return ret

def processTag(tagString, text, st, end):
    tupargs=[]
    dictargs={}
    tagname=''
    off=0

    tnmatch = None
    while not tnmatch:
        wsmatch = wsre.match(tagString, off, len(tagString))
        if not wsmatch:
            tnmatch = plainre.match(tagString, off, len(tagString))
            if not tnmatch:
                raise DTLexicalError( msg = 'invalid tag name', 
                                      tagtext = tagString,
                                      lineno = getLineno ( text, st ) )
            else:
                break
        off = wsmatch.end()
                                
    tagname=tnmatch.group()
    off=tnmatch.end()
    lts=len(tagString)
    while off<lts:
        match=tagContentsRe.match(tagString, off, lts)
        if match is None:
            raise DTLexicalError( msg = 'invalid tag text', tagtext = tagString,
                                  lineno = getLineno ( text, st ) )
        g=match.groupdict()
        
        tmp=g[WHITESPACE]
        if tmp is not None:
            off=match.end(WHITESPACE)
            continue
        
        tmp=g[PLAIN]
        if tmp is not None:
            tupargs.append(tmp)
            off=match.end(PLAIN)
            continue
        
        tmp=g[PLAINEQ]
        tmp2=g[PLAINEQVAL]
        if tmp is not None:
            assert tmp2 is not None
            dictargs[tmp]=tmp2
            off=match.end(PLAINEQVAL)
            continue

        tmp=g[PLAINEQQ]
        tmp2=g[PLAINEQQVAL]
        if tmp is not None:
            assert tmp2 is not None
            dictargs[tmp]=dequote(tmp2)
            off=match.end(PLAINEQQVAL)
            continue

        tmp=g[QUOTONLY]
        if tmp is not None:
            tupargs.append(dequote(tmp))
            off=match.end(QUOTONLY)
            continue


        raise DTLexicalError( msg = 'unknown text in tag', 
                              tagtext = tagString[off:off+10], 
                              lineno=getLineno(text, st) )

    return tagname, tupargs, dictargs

def getLineno(text, offset):
    f=StringIO.StringIO(text)
    bread=0
    lineno=0
    line=f.readline()
    while line:
        lineno=lineno+1
        bread=bread+len(line)
        if bread>offset:
            break
        line=f.readline()
    return lineno

def doTag(text, name):
    tl=[]
    tags=findTags(text)
    for tag in tags:
        if tag[2]:
            n,t,d=processTag(tag[3], text, tag[0], tag[1])
            tl.append(DTToken(text, name, (tag[0], tag[1], n, t, d)))
        else:
            tl.append(tag[3])
    return tl
        
if __name__=='__main__':
    import time
    
    text=open(sys.argv[1]).read()

    a=time.time()
    tl=doTag(text, '')
    print 'time:', time.time()-a
    print '-------------------'
    for i in tl:
        if type(i)==type(''):
            print 'S: |%s|' % i
        else:
            print 'tag:', i
