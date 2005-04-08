from threading import local

import skunk.config.scope as S
from skunk.util.decorators import with_lock

Configuration=local()
_scopeman=S.ScopeManager()

mergeDefaults=_scopeman.mergeDefaults
scope=_scopeman.scope


def Location(path, **kw):
    return S._createMatcher(S.SimpleStringMatcher,
                            'location',
                            path,
                            None,
                            kw)

def File(path, **kw):
    return S._createMatcher(S.RegexMatcher,
                            'location',
                            path,
                            None,
                            kw)

def Host(hostname, *kids, **kw):
    return S._createMatcher(S.GlobMatcher,
                            'host',
                            hostname,
                            kids,
                            kw)

def Port(port, *kids, **kw):
    return S._createMatcher(S.StrictMatcher,
                            'port',
                            port,
                            kids,
                            kw)

def ServerPort(port, *kids, **kw):
    return S._createMatcher(S.StrictMatcher,
                            'server_port',
                            port,
                            kids,
                            kw)

def IP(ip, *kids, **kw):
    return _createMatcher(scope.StrictMatcher,
                          'ip',
                          ip,
                          kids,
                          kw)

def UNIXPath(path, *kids, **kw):
    return S._createMatcher(S.GlobMatcher,
                            'unixpath',
                            path,
                            kids,
                            kw)                       


@with_lock(_scopeman._lock)
def load(*configfiles):
    g=_config_globals
    for c in configfiles:
        _scopeman.load(c, g)


_config_globals=dict(Scope=scope,
                     Include=load,
                     Location=Location,
                     Host=Host,
                     Port=Port,
                     ServerPort=ServerPort,
                     IP=IP,
                     UNIXPath=UNIXPath)
                 
                                             

def updateConfig(ctxt=None):
    Configuration.__dict__=_scopeman.getConfig(ctxt)


                


	
