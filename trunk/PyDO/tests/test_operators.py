"""

tests for the pydo.operators module.

(There are doctests in the module itself, so this is a bit spare at
the moment.)


"""
from testingtesting import tag
import config

alltags=config.ALLDRIVERS + ['operators']

from pydo.operators import *

@tag(*alltags)
def test_AND1():
    assert str(AND(FIELD('x')))=='x'

@tag(*alltags)               
def test_converter1():
    op=AND(FIELD('x'), EQ(FIELD('y'), 'fiddler\'s roof'))
    assert str(op)=="(x AND (y = 'fiddler''s roof'))"
    c=BindingConverter('qmark')
    op.setConverter(c)
    s=str(op)
    assert s=="(x AND (y = ?))"
    assert c.values==["fiddler's roof"]
