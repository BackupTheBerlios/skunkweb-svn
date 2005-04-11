import os



def getEnvironBase(instream,
                   errstream,
                   multithread=False,
                   multiprocess=True,
                   run_once=False):
    environ={}
    environ.update(os.environ)
    environ['wsgi.input']=instream
    environ['wsgi.errors']=errstream
    environ['wsgi.version']=(1,0)
    environ['wsgi.multithread']=multithread
    environ['wsgi.multiprocess']=multiprocess
    environ['wsgi.run_once']=run_once
    return environ
    
