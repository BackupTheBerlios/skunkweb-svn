"""

tests for the pydo.fields module.

"""
from testingtesting import tag
import config
alltags=config.ALLDRIVERS + ['fields']

import pydo as P

@tag(*alltags)
def test_getattr1():
    class A(P.PyDO):
        fields=(P.Sequence('id'), 'x')

    # this should not throw an error, although it did up through 2.0b0
    getattr(A, 'x')
    
