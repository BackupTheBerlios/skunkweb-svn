from xml.sax.saxutils import escape, unescape, quoteattr
from htmlentitydefs import entitydefs
import base64
import urllib

def xmlquote(s):
    'escapes &, <, >, and " with entity references'
    return escape(s, {'"' : '&quot;'})

htmlentitymap=dict([(y, '&%s;' % x) for x, y \
                    in entitydefs.iteritems() if y!='&'])

def htmlquote(s):
    'escapes everything possible into htmlentities'
    return escape(s, htmlentitymap)

def _latinquotechar(c):
    o=ord(c)
    if o>=160:
        return '&#%03d;' % o
    return c

def latinquote(s):
    """replaces all characters >=160 with character entities."""
    return ''.join(map(_latinquotechar, s))

def fullquote(s):
    """Escapes all characters to %XX format."""
    return (''.join(['%%%02x' % ord(x) for x in s])).upper()


ValFormatRegistry={'plain' : str,
                   'base64' : base64.encodestring,
                   'xml' : xmlquote,
                   'html' : htmlquote,
                   'latin' : latinquote,
                   'url' : urllib.quote,
                   'urlplus' : urllib.quote_plus,
                   'fullurl' : fullquote}

__all__=[x for x in locals() if x.endswith('quote')] + ['ValFormatRegistry']





