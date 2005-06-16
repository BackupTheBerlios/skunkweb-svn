"""
tests for the pydo.base module.

"""
from testingtesting import tag
import config
from fixture import Fixture
import pydo as P

alltags=config.ALLDRIVERS + ['base']

def _get_sequence_sql():
    return dict(sqlite='INTEGER NOT NULL',
                psycopg='SERIAL',
                mysql='INTEGER NOT NULL AUTO_INCREMENT')[config.DRIVER]


@tag(*alltags)
def test_inheritance1():
    class nougat(P.PyDO):
        schema='public'
        fields=(P.Sequence('id'),
                P.Unique('title'),
                'foo',
                'bar')
    class ripple(nougat):
        fields=('foople',
                'pinko')
    cols=set(('id',
              'title',
              'foo',
              'bar',
              'foople',
              'pinko'))
    assert set(ripple.getColumns())==cols
    uniq=frozenset(map(frozenset, (('id',), ('title',))))
    assert ripple.getUniquenessConstraints()==uniq
    assert ripple.getSequences()==dict(id=True)

@tag(*alltags)
def test_unique1():
    class baba(P.PyDO):
        fields=('x', 'y', 'z')
        unique=(('x', 'y'),)

    uniq=list(baba.getUniquenessConstraints())
    assert len(uniq)==1
    assert uniq[0]==frozenset(('x', 'y'))


class test_unique2(Fixture):
    tags=alltags[:]
    table='test_unique2'
    def setup(self):
        create="CREATE TABLE %s(id INTEGER UNIQUE NOT NULL, x INTEGER)" \
                % self.table
        c=self.db.cursor()
        c.execute(create)
        c.close()
        class foo(P.PyDO):
            connectionAlias='pydotest'
            table='test_unique2'
            fields=(P.Unique('id'), 'x')
        self.obj=foo
        for i in range(20):
            foo.new(id=i, x=100)

    def run(self):
        assert self.obj.getUnique(id=15).x==100
        assert self.obj.getUnique(id=800)==None


    def cleanup(self):
        if self.db.autocommit:
            c=self.db.cursor()
            c.execute('drop table %s' % self.table)
            c.close()
        else:
            self.db.rollback()
        
@tag(*alltags)        
def test_project1():
    class torte(P.PyDO):
        fields=(P.Sequence('id'),
                P.Unique('title'),
                'x',
                'y',
                'z')
    foo=torte.project('id', 'title', 'x')
    assert foo.getSequences()==dict(id=True)
    assert len(foo.getColumns())==3
    assert len(foo.getUniquenessConstraints())==2

@tag(*alltags)
def test_project2():
    class torte2(P.PyDO):
        fields=(P.Sequence('id'),
                P.Unique('title'),
                'x',
                'y',
                'z')
    assert not torte2._projections
    foo=torte2.project(P.Field('id'), 'title', 'x')
    assert not foo.getSequences(), "expected no sequences, got: %s" % str(foo.getSequences())
    assert len(foo.getUniquenessConstraints())==1

@tag(*alltags)
def test_project3():
    class A(P.PyDO):
        fields=(P.Sequence('id'), 'x')
    p=A.project(P.Field('id'))
    assert not p.getSequences()
    assert not p.getUniquenessConstraints()

@tag(*alltags)
def test_project4():
    class torte4(P.PyDO):
        fields=(P.Sequence('id'),
                'title',
                'x',
                'y',
                'z')
    foo=torte4.project(P.Field('id'), 'title', 'x', 'y')
    assert not foo.getSequences(), "expected no sequences, got: %s" % str(foo.getSequences())
    assert len(foo.getUniquenessConstraints())==0

@tag(*alltags)
def test_project5():
    create="""CREATE TABLE test_project5 (id INTEGER NOT NULL PRIMARY KEY, x INTEGER)"""
    insert="""INSERT INTO test_project5 (id, x) VALUES (1, 1)"""
    db=P.getConnection('pydotest')
    c=db.cursor()
    c.execute(create)
    c.execute(insert)
    try:
        class bingo(P.PyDO):
            connectionAlias='pydotest'
            table='test_project5'
            fields=(P.Sequence('id'), 'x')
        r1=bingo.getUnique(id=1)
        r1.refresh()
        r2=bingo.project('x').getSome()[0]
        try:
            r2.refresh()
        except ValueError:
            pass
        else:
            assert 0, "projection without unique constraint shouldn't be refreshable!"
    finally:
        if db.autocommit:
            c.execute('drop table test_project5')
        else:
            db.rollback()
        c.close()

@tag('sqlite', 'mysql', 'psycopg', 'base')        
def test_guess_columns1():
    create="""CREATE TABLE test_guess_columns1 (
    id %s PRIMARY KEY,
    x INTEGER NOT NULL UNIQUE,
    y INTEGER NOT NULL,
    z INTEGER UNIQUE,
    r1 INTEGER NOT NULL,
    r2 INTEGER NOT NULL,
    UNIQUE (r1, r2)
    )""" % _get_sequence_sql()
    
    db=P.getConnection('pydotest')
    c=db.cursor()
    c.execute(create)
    try:
        class testclass(P.PyDO):
            guess_columns=True
            table='test_guess_columns1'
            connectionAlias='pydotest'

        cols=testclass.getColumns()

        uniq=testclass.getUniquenessConstraints()
        #logging.debug('uniq: %s', str(uniq))
        seq=testclass.getSequences()
        assert set(cols)==set(('id', 'x', 'y', 'z', 'r1', 'r2'))
        assert seq.keys()==['id']
        assert uniq==frozenset((frozenset(('r1', 'r2')),
                                frozenset(('x',)),
                                frozenset(('id',))))

    finally:
        if db.autocommit:
            c.execute('drop table test_guess_columns1')
        else:
            db.rollback()
        c.close()                               

@tag(*alltags)
def test_unique1():
    class porkbarrel(P.PyDO):
        fields=(P.Sequence('a'),
                'b',
                'c')
        unique=(('b', 'c'),)
    u=porkbarrel.getUniquenessConstraints()
    assert len(u)==2
    assert frozenset(('b', 'c')) in u
    assert frozenset(('a',)) in u

@tag(*alltags)
def test_schema1():
    class A(P.PyDO):
        table='froggie'
        schema='pants'
    assert A.getTable(False)=='froggie'
    assert A.getTable(True)=='pants.froggie'
    assert A.getTable()=='pants.froggie'
    assert A.table=='froggie'
    assert A.schema=='pants'

@tag(*alltags)
def test_pickle1():
    global zingo
    class zingo(P.PyDO):
        fields=(P.Sequence('id'),
                'nohat',
                'nofrog',
                'pig')
    import cPickle
    dump=cPickle.dumps(zingo, 2)
    orig=cPickle.loads(dump)
    assert orig==zingo
    del zingo
        
class test_new1(Fixture):
    tags=alltags[:]
    class obj(P.PyDO):
        table='test_new1'
        connectionAlias='pydotest'
        fields=(P.Unique('id'), 'x')

    def setup(self):
        create=""" CREATE TABLE test_new1 (id INTEGER PRIMARY KEY NOT NULL,
        x INTEGER)"""
        c=self.db.cursor()
        c.execute(create)
        c.close()

    def cleanup(self):
        if self.db.autocommit:
            c=self.db.cursor()
            c.execute('DROP TABLE test_new1')
            c.close()
        else:
            self.db.rollback()

    def run(self):
        for i in range(100):
            self.obj.new(id=i, x=100)
        res=[x.id for x in self.obj.project('id').getSome(order='id')]
        assert res==range(100)
        
        
class test_update1(Fixture):
    tags=alltags[:]
    class obj(P.PyDO):
        table='test_update1'
        connectionAlias='pydotest'
        fields=(P.Sequence('id'),
                P.Unique('textcol1'),
                'textcol2',
                'textcol3')
        unique=(('textcol2', 'textcol3'),)

    def setup(self):
        create="""CREATE TABLE test_update1 (
        id %s,
        textcol1 VARCHAR(32) UNIQUE NOT NULL,
        textcol2 VARCHAR(32) NOT NULL,
        textcol3 VARCHAR(32) NOT NULL,
        UNIQUE(textcol2, textcol3)
        )""" % _get_sequence_sql()
        c=self.db.cursor()
        c.execute(create)
        c.close()

    def cleanup(self):
        if self.db.autocommit:
            c=self.db.cursor()
            c.execute('drop table test_update1')
            c.close()
        else:
            self.db.rollback()


    
        
