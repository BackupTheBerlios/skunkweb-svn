"""
a very very simple test framework.
"""

import re
import sys
import logging

logger=logging.getLogger('testingtesting')
exception=logger.exception
info=logger.info
logger.addHandler(logging.StreamHandler(sys.stderr))

_defaultNamePat=re.compile(r'^test')

def _testsForModule(m, namePat, tags):
    return _testsForNamespace(vars(m), namePat, *tags)

def _testsForNamespace(ns, namePat, tags):
    for name, value in sorted(ns.iteritems()):
        if callable(value) and namePat.search(name):
            ftags=getattr(value, 'tags', None)
            if not ftags:
                yield value
            else:
                if set(tags).issubset(ftags):
                    yield value
            
def runtests(tests):
    success=[]
    fail=[]
    for i, t in enumerate(tests):
        i+=1
        info('running test no %d (%s)', i, t.__name__)
        try:
            t()
        except:
            exception("test no. %d (%s)  failed", i, t.__name__)
            fail.append((t, sys.exc_info()))
        else:
            info('test %s passed', t.__name__)
            success.append(t)
    summarize_tests(success, fail)
    if fail:
        return 1
    return 0

def runModule(m, tags=None, namePat=_defaultNamePat):
    return runtests(_testsForModule(m, namePat, tags))

def runNamespace(tags=None, ns=None, namePat=_defaultNamePat):
    if ns is None:
        ns=globals()
    return runtests(_testsForNamespace(ns, namePat, tags))

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

def tag(*tags):
    """ decorator for tests """
    def wrapper(func):
        func.tags=tags
        return func
    return wrapper


__all__=['runModule', 'runNamespace', 'info', 'tag']    

@tag('choo')    
def test_anything():
    assert 1==1

@tag('foo')
def test_anotherthing():
    # this one will fail
    assert 2==1, "2 should equal 1"

@tag('foo', 'choo')
def test_exception():
    try:
        1 / 0
    except ZeroDivisionError:
        x=1
    else:
        x=0
    assert x==1

if __name__=='__main__':
    tags=sys.argv[1:]
    logger.setLevel(logging.INFO)
    info('running tests')
    res=runNamespace(tags)
    sys.exit(res)
    
    
    
