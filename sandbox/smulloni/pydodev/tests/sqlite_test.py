import os
import subprocess
import unittest

SQLITE_DB=os.environ.get('PYDO_SQLITE_TEST_DB', '/tmp/pydo_sqlite_test.db')

import sys
sys.path.append('../src')
from PyDO import *

class base(PyDO):
    connectionAlias="sqlitetest"

class PyDOGroup(base):
    table="pydogroup"
    auto_increment={'id' : 1}
    unique=['id', 'groupname']
    fields=(('id', 'int'),
            ('groupname', 'text'))
    

class PyDOUser(base):

    table='pydouser'
    auto_increment={'id' : 1}
    unique=['id']
    fields=('id',
            'firstname',
            'lastname')


class Article(base):
    table="article"
    auto_increment={'id': 1}
    unique=['id']
    fields=(('id', 'int'),
            ('title', 'text'),
            ('body', 'text'),
            ('creator', 'int'),
            ('created', 'timestamp'))

initAlias('sqlitetest', 'sqlite', dict(database=SQLITE_DB), verbose=True)
import logging
logging.basicConfig()
from PyDO.log import debug, logger
logger.setLevel(logging.DEBUG)
logging.debug("hi there")

def _initDB():
    if os.path.exists(SQLITE_DB):
        os.remove(SQLITE_DB)
    sqlpath=os.path.join(os.path.dirname(__file__), 'sqlite.sql')
    fp=open(sqlpath)
    p=subprocess.Popen(['sqlite', SQLITE_DB], stdin=fp)
    p.communicate()    

class SqliteTest(unittest.TestCase):
    def setUp(self):
        _initDB()
        
    def tearDown(self):
        os.remove(SQLITE_DB)

    def runTest(self):
        pass

    def test_insert(self):
        users=[PyDOUser.new(refetch=1,
                            firstname='Colin',
                            lastname='Powell'),
               PyDOUser.new(refetch=1,
                            firstname='Richard',
                            lastname='Clark'),
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

if __name__=='__main__':
    unittest.main()
                        
