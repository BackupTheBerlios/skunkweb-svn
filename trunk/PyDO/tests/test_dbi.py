"""
Tests for the pydo.dbi module.

"""
import threading

from testingtesting import tag
from config import ALLDRIVERS
dbitags=ALLDRIVERS+['dbi']
import pydo.dbi as D

@tag(*dbitags)
def test_initAlias1():
    """ calls initAlias with bogus arguments.  Should succeed."""    
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
    D.delAlias('jackandjill')

@tag(*dbitags)
def test_threads1():
    """
    tests that each thread gets its own dbapi connection.
    """
    db=D.getConnection('pydotest')
    id1=id(db.conn)

    class mythread(threading.Thread):
        def run(self):
            mydb=D.getConnection('pydotest')
            self.connid=id(mydb.conn)
    t=mythread()
    t.start()
    t.join()
    assert t.connid!=id1
    assert id(db.conn)==id1

#@tag(*dbitags)    
#def test_pool1():
#    """
#    creates a pool, gets a connection from it, stores its id.  Starts a thread
#    and gets 
#    """
#    pass
