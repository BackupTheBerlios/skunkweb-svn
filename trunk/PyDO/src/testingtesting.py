"""
a very very simple test framework.
"""

import sys
import logging

logger=logging.getLogger('testingtesting')
exception=logger.exception
info=logger.info
logger.addHandler(logging.StreamHandler(sys.stderr))

def defaultCriterion(n, f):
    return n.startswith('test') and callable(f)

def _testsForModule(m, func=defaultCriterion):
    return _testsForNamespace(vars(m), func)


def _testsForNamespace(n, func=defaultCriterion, attrname='tags', *tags):
    all=(x[1] for x in sorted((i for i in n.iteritems() if func(*i)),
                              key=lambda x: x[0]))
    for a in all:
        ftags=getattr(a, attrname, None)
        if not ftags:
            yield a
        else:
            if set(tags).subset(ftags):
                yield a
    
    

def runtests(tests):
    success=[]
    fail=[]
    for i, t in enumerate(tests):
        i+=1
        try:
            t()
        except:
            exception("test no. %d (%s)  failed", i, t.__name__)
            fail.append((t, sys.exc_info()))
        else:
            success.append(t)
    summarize_tests(success, fail)
    if fail:
        return 1
    return 0

def runModule(m):
    return runtests(_testsForModule(m))

def runNamespace(n=None):
    if n is None:
        n=globals()
    return runtests(_testsForNamespace(n))

def summarize_tests(success, fail):
    total=len(success)+len(fail)
    if total == 1:
        TESTS='test'
    else:
        TESTS='tests'
    info("%d %s run; passed: %d, failed: %d",
         total,
         TESTS,
         len(success),
         len(fail))

__all__=['runModule', 'runNamespace', 'info']    
    
    
def test_anything():
    assert 1==1

def test_anotherthing():
    # this one will fail
    assert 2==1, "2 should equal 1"

def test_exception():
    try:
        1 / 0
    except ZeroDivisionError:
        x=1
    else:
        x=0
    assert x==1

def annotate(attrname, *tags):
    """ decorator for tests """
    def wrapper(func):
        setattr(f, attrname, tags)
        return f
    return wrapper

if __name__=='__main__':
    logger.setLevel(logging.INFO)
    info('running tests')
    res=runNamespace()
    sys.exit(res)
    
    
    
