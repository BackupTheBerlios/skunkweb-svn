import skunk.config as C


def test_scope1():
    class bag(object):
        def __init__(self, kw):
            self.__dict__.update(kw)
            
    man=C.ScopeManager()
    m.mergeDefaults(foo=1,
                    goo=2,
                    poo=3)
    m.loads("foo=4\ngoo=400\n")
    c=bag(m.getConfig())
    assert c.foo==4
    assert c.goo==400
    assert c.poo==3

    
