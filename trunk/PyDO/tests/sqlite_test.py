import os
import random
import subprocess
import unittest
import logging
import sys
sys.path.append('../src')
from PyDO import *

SQLITE_DB=os.environ.get('PYDO_SQLITE_TEST_DB', '/tmp/pydo_sqlite_test.db')
class base(PyDO):
    connectionAlias="sqlitetest"

commit=base.commit
rollback=base.rollback

class PyDOGroup(base):
    table="pydogroup"
    auto_increment={'id' : 1}
    unique=['id', 'groupname']
    fields=(('id', 'int'),
            ('groupname', 'text'))

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
    auto_increment={'id' : 1}
    unique=['id']
    fields=('id',
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
    auto_increment={'id': 1}
    unique=['id']
    fields=(('id', 'int'),
            ('title', 'text'),
            ('body', 'text'),
            ('creator', 'int'),
            ('created', 'timestamp'))


logging.basicConfig()
setLogLevel(logging.DEBUG)

def _initDB():
    if os.path.exists(SQLITE_DB):
        os.remove(SQLITE_DB)
    sqlpath=os.path.join(os.path.dirname(__file__), 'sqlite.sql')
    fp=open(sqlpath)
    # I'm sure I could do this directly with pysqlite, too....    
    p=subprocess.Popen(['sqlite', SQLITE_DB], stdin=fp)
    p.communicate()    


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


def _init_data():
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
                                        body=_concoctBody()))
    commit()


class SqliteTest(unittest.TestCase):

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

initAlias('sqlitetest', 'sqlite', dict(database=SQLITE_DB), verbose=True)        

if __name__=='__main__':
    _initDB()
    _init_data()
    unittest.main()
                        
