from test_base import *
import subprocess

SQLITE_DB=os.environ.get('PYDO_SQLITE_TEST_DB', '/tmp/pydo_sqlite_test.db')

def _initDB():
    if os.path.exists(SQLITE_DB):
        os.remove(SQLITE_DB)
    sqlpath=os.path.join(os.path.dirname(__file__), 'sqlite.sql')
    fp=open(sqlpath)
    # I'm sure I could do this directly with pysqlite, too....    
    p=subprocess.Popen(['sqlite', SQLITE_DB], stdin=fp)
    p.communicate()    

base.connectionAlias='sqlitetest'    

initAlias('sqlitetest', 'sqlite', dict(database=SQLITE_DB), cache=True, verbose=True)        

if __name__=='__main__':
    _initDB()
    init_data()
    unittest.main()

