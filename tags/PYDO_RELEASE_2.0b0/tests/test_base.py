"""
tests for the pydo.base module.

"""
from testingtesting import tag
import config
from fixture import Fixture, base_fixture, get_sequence_sql
import pydo as P

import random
import string
import sys

def ranwords(num, length=9):
    s=set()
    while len(s)<length:
        s.add(''.join(random.sample(string.ascii_lowercase, length)))
    return s


alltags=config.ALLDRIVERS + ['base']


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

class test_unique2(base_fixture):
    usetables=['D']
    tags=alltags

    def pre(self):
        for i in range(20):
            self.D.new(id=i, x=100)
        

    def run(self):
        assert self.D.getUnique(id=15).x==100
        assert self.D.getUnique(id=800)==None
        
        
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

class test_project5(base_fixture):
    usetables=['D']
    tags=alltags

    def pre(self):
        self.D.new(id=1, x=1)

    def run(self):
        r1=self.D.getUnique(id=1)
        r1.refresh()
        r2=self.D.project('x').getSome()[0]
        try:
            r2.refresh()
        except ValueError:
            pass
        else:
            assert 0, "projection without unique constraint shouldn't be refreshable!"
            
@tag('sqlite', 'mysql', 'psycopg', 'base')        
def test_guess_columns1():
    create="""CREATE TABLE test_guess_columns1 (
    id %s,
    x INTEGER NOT NULL UNIQUE,
    y INTEGER NOT NULL,
    z INTEGER UNIQUE,
    r1 INTEGER NOT NULL,
    r2 INTEGER NOT NULL,
    UNIQUE (r1, r2)
    )""" % get_sequence_sql()
    
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


class test_new2(base_fixture):
    usetables=('A',)
    tags=alltags

    def run(self):
        res=self.A.newfetch(name='porkhat',
                            x=4,
                            y=5,
                            z=20)
        assert res.d==33
        res=self.A.newnofetch(name='pinger',
                              x=50,
                              y=100,
                              z=0)
        assert res.d==None
        


class test_update1(base_fixture):
    tags=alltags
    usetables=['A']

    def pre(self):
        for i, w in enumerate(ranwords(100)):
            if i % 2:
                ta=None
            else:
                ta=w.upper()
            self.A.new(name=w,
                       ta=ta,
                       x=i,
                       y=i+100,
                       z=40)

    def run(self):
        all=self.A.getSome()
        for a in all:
            a.tb='choo choo'
                       

class test_deleteSome1(base_fixture):
    usetables=('B',)
    tags=alltags

    def pre(self):
        for x in xrange(200):
            self.B.new(x=random.randint(0, 1000))

    def run(self):

        self.B.deleteSome(P.LT(P.FIELD('x'), 500))
        sql='SELECT COUNT(*) FROM b WHERE x < 500'
        c=self.db.cursor()
        c.execute(sql)
        cnt=c.fetchone()[0]
        assert cnt==0


class test_updateSome1(base_fixture):
    usetables=('B',)
    tags=alltags
    
    def pre(self):
        for x in xrange(200):
            self.B.new(x=random.randint(0, 1000))
        c=self.db.cursor()
        sql='SELECT COUNT(*) FROM b WHERE x < 500'
        c.execute(sql)
        self.count=c.fetchone()[0]
        c.close()

    def run(self):

        self.B.updateSome(dict(x=None), P.LT(P.FIELD('x'), 500))
        sql='SELECT COUNT(*) FROM b WHERE x IS NULL'
        c=self.db.cursor()
        c.execute(sql)
        nullcnt=c.fetchone()[0]
        assert nullcnt==self.count


class test_delete1(base_fixture):
    usetables=('C',)
    tags=alltags

    def pre(self):
        self.objs=[self.C.new(x=i) for i in range(100)]

    def run(self):
        for o in self.objs:
            i=o.id
            o.delete()
            assert not o.mutable
            o1=self.C.getUnique(id=i)
            assert o1 is None

class test_delete2(base_fixture):
    usetables=('C',)
    tags=alltags

    def pre(self):
        self.C.new(id=100, x=1)

    def run(self):
        proj=self.C.project('x')
        o=proj.getSome(order='id DESC', limit=1)[0]
        try:
            o.delete()
        except ValueError:
            pass
        else:
            assert 0, \
                   ('expected ValueError to be raised '
                    'when deleting an object without a '
                    'unique constraint')
            

class test_joinTable1(base_fixture):
    usetables=('A', 'C', 'A_C')
    tags=alltags

    def pre(self):
        insert=["""INSERT INTO a (id, b_id, name, x, y, z) VALUES (1, NULL, 'poco a poco', 3, 5, 2)""",
                """INSERT INTO a (id, b_id, name, x, y, z) VALUES (2, 1, 'mammoth', 30, 20, 1000)""",
                """INSERT INTO c (id, x) VALUES (1, 100)""",
                """INSERT INTO a_c (a_id, c_id) VALUES (2, 1)"""]
        c=self.db.cursor()
        for i in insert:
            c.execute(i)

    def run(self):
        o1=self.A.getUnique(id=1)
        assert o1 is not None
        j=o1.joinTable('id', 'a_c', 'a_id', 'c_id', self.C, 'id')
        assert len(j)==0
        o2=self.A.getUnique(id=2)
        assert o2 is not None
        j=o2.joinTable('id', 'a_c', 'a_id', 'c_id', self.C, 'id')
        assert len(j)==1
        assert j[0].id==1
        
class test_getSome1(base_fixture):
    usetables=('A',)
    tags=alltags

    def pre(self):
        self.A.new(name='MAX FACTOR',
                   b_id=5,
                   d=55,
                   x=0,
                   y=1,
                   z=2)

        self.A.new(name='HORTENSE MAXIMUS',
                   b_id=60,
                   d=0,
                   x=40,
                   y=50,
                   z=60)

        self.A.new(name='TENSION EXTREMUS',
                   b_id=-100,
                   x=40,
                   y=-80,
                   z=6000)

    def run(self):
        r=self.A.getSome()
        assert len(r)==3
        r=self.A.getSome('id <2')
        assert len(r)==1
        assert r[0].d==55
        r=self.A.getSome(P.EQ(P.FIELD('d'), 55))
        assert len(r)==1
        assert r[0].x==0
        r=self.A.getSome(P.OR(P.LT(P.FIELD('y'), 0),
                              P.LIKE(P.FIELD('name'), '%MAX%')))
        assert len(r)==3
        r=self.A.getSome(P.LIKE(P.FIELD('name'), '%TENS%'), order='z DESC')
        assert len(r)==2
        assert r[0].z==6000
        assert r[1].z==60

class test_refresh1(base_fixture):
    usetables=('A',)
    tags=alltags

    def pre(self):
        self.obj=self.A.new(name='bingo junction',
                            b_id=4,
                            ta=300,
                            x=0,
                            y=30,
                            z=-1)

    def run(self):
        assert self.obj.d is None
        self.obj.refresh()
        assert self.obj.d==33

        

        
        




