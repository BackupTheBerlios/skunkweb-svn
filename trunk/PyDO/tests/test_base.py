import os
import mx.DateTime
import random
import unittest
import logging
import sys
sys.path.append('../src')
from PyDO import *


class base(PyDO):
    pass

commit=base.commit
rollback=base.rollback

class PyDOGroup(base):
    table="pydogroup"
    fields=(Sequence('id'),
            'groupname')

    def getUsers(self):
        return self.joinTable('id',
                              'pydouser_pydogroup',
                              'group_id',
                              'user_id',
                              PyDOUser,
                              'id')

class user_group(base):
    table="pydouser_pydogroup"
    unique=[('user_id', 'group_id')]
    fields=('user_id',
            'group_id')

class PyDOUser(base):

    table='pydouser'
    fields=(Sequence('id'),
            'firstname',
            'lastname')

    def getGroups(self):
        return self.joinTable('id',
                              'pydouser_pydogroup',
                              'user_id',
                              'group_id',
                              PyDOGroup,
                              'id')

    def getArticles(self):
        return Article.getSome(creator=self.id, order='created DESC')


class Article(base):
    table="article"
    fields=(Sequence('id'),
            'title',
            'body',
            'creator',
            'created')


logging.basicConfig()
setLogLevel(logging.DEBUG)

WORDS=('ingot',
       'plum',
       'justice',
       'horticulture',
       'frog',
       'appendage',
       'cultivation',
       'oyster',
       'Mr.',
       'Mrs.',
       'Ms.',
       'tense',
       'laudatory',
       'infest',
       'row',
       'ascend',
       'cockroach',
       'ham',
       'turtle',
       'overloading',
       'screeching',
       'handed',
       'lost',
       'purchase',
       'egg')

def _inventTitle(min_=5, max_=12):
    val=min(len(WORDS), random.randint(min_, max_))
    return " ".join(random.sample(WORDS, val)).capitalize()

def _concoctBody():
    return ". ".join([_inventTitle(5, 50) for x in xrange(random.randint(10, 100))])


def init_data():
    users=[PyDOUser.new(refetch=1,
                        firstname='Colin',
                        lastname='Powell'),
           PyDOUser.new(refetch=1,
                        firstname='Richard',
                        lastname='Clarke'),
           PyDOUser.new(refetch=1,
                        firstname='Jacques',
                        lastname='Chirac'),
           PyDOUser.new(refetch=1,
                        firstname='Goldie',
                        lastname='Hawn')]
    groups=[PyDOGroup.new(refetch=1,
                          groupname='ForkLovers'),
            PyDOGroup.new(refetch=1,
                          groupname='SpoonLovers'),
            PyDOGroup.new(refetch=1,
                          groupname='KnifeLovers'),
            PyDOGroup.new(refetch=1,
                          groupname='ChopstickLovers'),
            PyDOGroup.new(refetch=1,
                          groupname='HandLovers')]

    # each user joins two groups at random
    for u in users:
        for x in random.sample(groups, 2):
            user_group.new(user_id=u.id, group_id=x['id'])

    articles=[]
    for u in users:
        for i in range(random.randint(2, 10)):
            articles.append(Article.new(refetch=1,
                                        creator=u.id,
                                        title=_inventTitle(),
                                        body=_concoctBody(),
                                        created=mx.DateTime.now()))
    commit()


class BaseTest(unittest.TestCase):

    def test_getSome(self):
        a=Article.getSome(order=['creator', 'id'])
        self.assert_(len(a))
        u=PyDOUser.getSome()
        self.assert_(len(u))
        a2=[x.getArticles() for x in u]
        self.assertEqual(sum([len(x) for x in a2]), len(a))
        
    def test_delete(self):
        for article in Article.getSome():
            article.delete()
        self.assertEqual(len(Article.getSome()), 0)
        rollback()

    def test_update(self):
        for a in Article.getSome(creator=1):
            a.title="Blah Blah"
        self.assertEqual(len(Article.getSome(title='Blah Blah')),
                         len(Article.getSome(creator=1)))
        rollback()

    def test_join(self):
        groups=PyDOGroup.getSome()
        for u in PyDOUser.getSome():
            u.getGroups()

    def test_project(self):
        projection=Article.project(('id', 'title'))
        a=projection.getSome()
        self.assertEqual(len(a),
                         len(Article.getSome()))
        self.assertEqual(2, len(projection.getColumns()))


    def test_time1(self):
        projection=Article.project(('id', 'created', 'creator'))
        a=projection.getSome(LT_EQ(FIELD('created'), mx.DateTime.now()))

    def test_time2(self):
        res=Article.getSome(created=mx.DateTime.now())
        self.assertEqual(0, len(res))

    def test_time3(self):
        res=Article.getSome(LT(FIELD('created'), mx.DateTime.now()+1))
        logging.debug('results: %s', (res,))
        self.assert_(len(res))
        

        
    


                        
