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

@tag(*dbitags)
def test_swapConnection1():
    db=D.getConnection('pydotest')
    conn1=db._connect()
    conn2=db.conn
    assert not (conn1 is conn2)
    conn3=db.swapConnection(conn1)
    assert conn3 is conn2
    assert conn1 is db.conn


@tag(*dbitags)    
def test_pool1():
    stuff=D._aliases['pydotest'].copy()
    D.initAlias('pydotestpool',
                stuff['driver'],
                stuff['connectArgs'],
                D.ConnectionPool(max_poolsize=4, keep_poolsize=4),
                stuff['verbose'])
    db=D.getConnection('pydotestpool')
    try:
        assert len(db.pool._busy)==0
        assert len(db.pool._free)==0
        conn=db.conn
        assert len(db.pool._busy)==1
        assert len(db.pool._free)==0
        c=conn.cursor()
        c.execute('SELECT 1+1')
        res=c.fetchone()
        assert res[0]==2
        c.close()
        conn.close()
        assert len(db.pool._busy)==0
        assert len(db.pool._free)==1
    finally:
        D.delAlias('pydotestpool')
