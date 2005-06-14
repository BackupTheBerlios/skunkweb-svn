"""
tests for the pydo.base module.

"""

from testingtesting import tag
from config import ALLDRIVERS
alltags=ALLDRIVERS + ['base']
import pydo as P

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

def test_unique1():
    class baba(P.PyDO):
        fields=('x', 'y', 'z')
        unique=(('x', 'y'),)

    uniq=list(baba.getUniquenessConstraints())
    assert len(uniq)==1
    assert uniq[0]==frozenset(('x', 'y'))


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

def test_project3():
    class A(P.PyDO):
        fields=(P.Sequence('id'), 'x')
    p=A.project(P.Field('id'))
    assert not p.getSequences()
    assert not p.getUniquenessConstraints()

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
        
