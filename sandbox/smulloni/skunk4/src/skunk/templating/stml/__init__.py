"""

An implementation of STML (Skunk Template Markup Language), the
templating language originally invented by Drew Csillag as part of
SkunkWeb (http://skunkweb.org/).  

"""

from skunk.templating.stml.exceptions import *
from skunk.templating.stml.lexer import *
from skunk.templating.stml.codeStream import *
from skunk.templating.stml.parser import *
from skunk.templating.stml.tagutils import *
from skunk.templating.stml.signature import *
from skunk.templating.stml.valformat import *
from skunk.templating.stml.tags import *
from skunk.templating.stml.comp import *

# __all__ is the union of all submodules' __all__.
try:
    from types import ModuleType
    __all__=reduce(lambda x, y: x+y, [getattr(v, '__all__', []) \
                                      for v in locals().values() \
                                      if isinstance(v, ModuleType)])
    del ModuleType
except TypeError:
    # pydoc seems to run into this problem
    pass

