import os
import mx.DateTime
import random
import unittest
import logging
import sys
import time
sys.path.append('../src')
from pydo import *

class base(PyDO):
    pass

commit=base.commit
rollback=base.rollback

class PyDOGroup(base):
    fields=(Sequence('id'),
            'groupname')
    refetch=True

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
    fields=(Sequence('id'),
            'firstname',
            'lastname')
    refetch=True

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
    refetch=True
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


def init_data(PyDOUser=PyDOUser,
              PyDOGroup=PyDOGroup,
              user_group=user_group,
              Article=Article):
    users=[PyDOUser.new(firstname='Colin',
                        lastname='Powell'),
           PyDOUser.new(firstname='Richard',
                        lastname='Clarke'),
           PyDOUser.new(firstname='Jacques',
                        lastname='Chirac'),
           PyDOUser.new(firstname='Goldie',
                        lastname='Hawn')]
    groups=[PyDOGroup.new(groupname='ForkLovers'),
            PyDOGroup.new(groupname='SpoonLovers'),
            PyDOGroup.new(groupname='KnifeLovers'),
            PyDOGroup.new(groupname='ChopstickLovers'),
            PyDOGroup.new(groupname='HandLovers')]

    # each user joins two groups at random
    for u in users:
        for x in random.sample(groups, 2):
            user_group.new(user_id=u.id, group_id=x['id'])

    articles=[]
    for u in users:
        for i in range(random.randint(2, 10)):
            articles.append(Article.new(creator=u.id,
                                        title=_inventTitle(),
                                        body=_concoctBody(),
                                        created=mx.DateTime.now()))
    commit()


class Tests(unittest.TestCase):
    def setUp(self):
        self.Article=Article
        self.PyDOUser=PyDOUser
        self.user_group=user_group
        self.PyDOGroup=PyDOGroup
                 
    def test_getSome(self):
        a=self.Article.getSome(order=['creator', 'id'])
        self.assert_(len(a))
        u=self.PyDOUser.getSome()
        self.assert_(len(u))
        a2=[x.getArticles() for x in u]
        self.assertEqual(sum([len(x) for x in a2]), len(a))
        
    def test_delete(self):
        for article in self.Article.getSome():
            article.delete()
        self.assertEqual(len(self.Article.getSome()), 0)
        rollback()

    def test_update(self):
        for a in self.Article.getSome(creator=1):
            a.title="Blah Blah"
        self.assertEqual(len(self.Article.getSome(title='Blah Blah')),
                         len(self.Article.getSome(creator=1)))
        rollback()

    def test_join(self):
        groups=self.PyDOGroup.getSome()
        for u in self.PyDOUser.getSome():
            u.getGroups()

    def test_project(self):
        projection=self.Article.project(('id', 'title'))
        a=projection.getSome()
        self.assertEqual(len(a),
                         len(self.Article.getSome()))
        self.assertEqual(2, len(projection.getColumns()))


    def test_time1(self):
        projection=self.Article.project(('id', 'created', 'creator'))
        a=projection.getSome(LT_EQ(FIELD('created'), mx.DateTime.now()))

    def test_time2(self):
        time.sleep(1)
        res=self.Article.getSome(created=mx.DateTime.now())
        self.assertEqual(0, len(res))

    def test_time3(self):
        res=self.Article.getSome(LT(FIELD('created'), mx.DateTime.now()+1))
        logging.debug('results: %s', (res,))
        self.assert_(len(res))
        

        
    


                        
