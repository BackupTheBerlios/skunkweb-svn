"""
Tests for the pydo.dbi module.

"""

from testingtesting import tag
from config import ALLDRIVERS
dbitags=ALLDRIVERS+['dbi']

@tag(*dbitags)
def test_initAlias1():
    """ calls initAlias with bogus arguments.  Should succeed."""    
    import pydo.dbi as D
    alias='pomposity'
    D.initAlias(alias, 'anything', 'anything', True, True)
    try:
        assert D._aliases.has_key(alias)
    finally:
        D.delAlias(alias)
        assert not D._aliases.has_key(alias)

@tag(*dbitags)    
def test_initAlias2():
    """ calls initAlias twice with the same arguments.  Should succeed. """
    import pydo.dbi as D
    alias='fruitcake'
    driver='pong'
    connectArgs='blimp'
    
    D.initAlias(alias, driver, connectArgs)
    try:
        try:
            D.initAlias(alias, driver, connectArgs)
        except ValueError:
            raise ValueError, \
                  "ValueError should not be raised when an alias is reinitialized"\
                  " with identical data!"
        
    finally:
        D.delAlias(alias)

@tag(*dbitags)
def test_initAlias3():
    """ calls initAlias twice with different arguments.  Should fail. """
    import pydo.dbi as D
    alias='fruitcake'
    driver='pong'
    connectArgs='blimp'
    D.initAlias(alias, driver, connectArgs)
    connectArgs='potato'
    try:
        try:
            D.initAlias(alias, driver, connectArgs)
        except ValueError:
            error_raised=True
        else:
            error_raised=False
        assert error_raised, \
               "ValueError should be raised when a change is made to alias config"
    finally:
        D.delAlias(alias)

@tag(*dbitags)
def test_delAlias1():
    """ calls delAlias for an alias that does not exist. Should succeed."""
    import pydo.dbi as D
    D.delAlias('jackandjill')


    
