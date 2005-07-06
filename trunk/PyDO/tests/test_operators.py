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

               
