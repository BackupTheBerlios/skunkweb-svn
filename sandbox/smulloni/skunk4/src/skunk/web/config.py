from threading import local

import skunk.config.scope as S
from skunk.util.decorators import with_lock

_scopeman=S.ScopeManager()

Configuration=local()
mergeDefaults=_scopeman.mergeDefaults
scope=_scopeman.scope

def _createMatcher(matcherClass, paramName, paramVal, kids, kw):
    m=matcherClass(paramName, paramVal, kw)
    if kids:
        m.addChildren(*kids)
    return m

def Location(path, **kw):
    return _createMatcher(S.SimpleStringMatcher,
                          'LOCATION',
                          path,
                          None,
                          kw)

def File(path, **kw):
    return _createMatcher(S.RegexMatcher,
                          'LOCATION',
                          path,
                          None,
                          kw)

def Host(hostname, *kids, **kw):
    return _createMatcher(S.GlobMatcher,
                          'HOST',
                          hostname,
                          kids,
                          kw)

def Port(port, *kids, **kw):
    return _createMatcher(S.StrictMatcher,
                          'PORT',
                          port,
                          kids,
                          kw)

def ServerPort(port, *kids, **kw):
    return _createMatcher(S.StrictMatcher,
                          'SERVER_PORT',
                          port,
                          kids,
                          kw)

def IP(ip, *kids, **kw):
    return _createMatcher(S.StrictMatcher,
                          'IP',
                          ip,
                          kids,
                          kw)

def UnixSocketPath(path, *kids, **kw):
    return _createMatcher(S.GlobMatcher,
                          'UNIX_SOCKET_PATH',
                          path,
                          kids,
                          kw)                       

@with_lock(_scopeman._lock)
def loadConfig(*configfiles):
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
                     UnixSocketPath=UnixSocketPath)
                 
def updateConfig(ctxt=None):
    Configuration.__dict__=_scopeman.getConfig(ctxt)


__all__=['Configuration',
         'mergeDefaults',
         'scope',
         'loadConfig',
         'updateConfig']


	
