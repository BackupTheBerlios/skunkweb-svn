from test_base import *
import subprocess

POSTGRES_DB="pydotest"

base.connectionAlias='postgrestest'


class PyDOGroup(PyDOGroup):
    fields=(Sequence('id', 'pydogroup_id_seq'),)
    
    def getUsers(self):
        return self.joinTable('id',
                              'pydouser_pydogroup',
                              'group_id',
                              'user_id',
                              PyDOUser,
                              'id')

class PyDOUser(PyDOUser):
    fields=(Sequence('id', 'pydouser_id_seq'),)

    def getGroups(self):
        return self.joinTable('id',
                              'pydouser_pydogroup',
                              'user_id',
                              'group_id',
                              PyDOGroup,
                              'id')

    def getArticles(self):
        return Article.getSome(creator=self.id, order='created DESC')

class Tests(Tests):
    def setUp(self):
        self.Article=Article
        self.PyDOUser=PyDOUser
        self.user_group=user_group
        self.PyDOGroup=PyDOGroup    

class Article(Article):
    fields=(Sequence('id', 'article_id_seq'),)

def _initDB():
    script=os.path.join(os.path.dirname(__file__), 'postgres_init.sh')
    p=subprocess.Popen(['/bin/bash', script], stdout=subprocess.PIPE)
    p.communicate()

initAlias('postgrestest',
          'psycopg',
          "dbname=pydotest user=pydotest",
          pool=True,
          verbose=True)        

if __name__=='__main__':
    _initDB()
    init_data(PyDOUser, PyDOGroup, user_group, Article)
    unittest.main()
                        
