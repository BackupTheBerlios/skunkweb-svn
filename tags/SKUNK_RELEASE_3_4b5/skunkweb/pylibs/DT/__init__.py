#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
This package is the rendering library for the
STML templating langauge used by the SkunkWeb server.

This is the core of the STML templating library -- 
that is, we don't have all the tags, but we do have the 
basic ones.  (The rest of the tags are implemented in
the SkunkWeb services.) In here is where the STML->python
byte-code compiler and runtime environment is.
"""

from DT import *
from DTExcept import DTRuntimeError, DTCompileError, DTLexicalError
