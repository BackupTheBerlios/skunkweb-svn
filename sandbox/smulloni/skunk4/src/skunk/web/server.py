
import grp
import logging
import os
import pwd
import sys

from skunk.net.server.socketmgr import SocketManager
from skunk.web.config import Configuration, loadConfig, updateConfig, mergeDefaults
from skunk.util.hooks import Hook

"""

Bootstrap does need a spot to configure the logging.  A separate conf
file, I suppose; at least until I figure out a better way of dealing
with configuration.

"""
ChildStart=Hook()

class Server(SocketManager):
    """ the skunkweb server itself."""
    def __init__(self, *configFiles):
        super(Server, self).__init__(Configuration.pidFile,
                                     Configuration)
        self.configFiles=configFiles
        
    def run(self):
        ChildStart()
        super(Server, self).run()

    def reload(self):
        super(Server, self).reload()
        configLogging()
        loadServices()
        loadConfig(*self.configFiles)
        configDefaults()

def configDefaults():
    mergeDefaults(pidFile='/tmp/skunk_server.pid',
                  run_group=None,
                  run_user=None,
                  services=(),
                  jobs=())

_svr=None


def loadServices():
    for servicename in Configuration.services:
        __import__(servicename)
        mod=sys.modules[servicename]
        if hasattr(mod, 'serviceInit'):
            mod.serviceInit()


def configLogging():
    
    # a placeholder; this should have better defaults and also look
    # for a logging config file.  because of the latter, which is
    # probably configuration dependent, perhaps this should happen
    # after the configuration is loaded
    # TO BE DONE    
    #logging.basicConfig()
    pass


def init(*configFiles):
    global _svr
    if _svr:
        raise RuntimeError, "already initialized"

    configLogging()
    loadConfig(*configFiles)
    configDefaults()
    updateConfig()

    # set effective user/group, if necessary
    isroot=os.getuid()==0
    run_user=Configuration.run_user
    run_group=Configuration.run_group
    if isroot and run_user is None:
        raise RuntimeError, "won't run as root with out run_user being defined"
    if run_group is not None:
        gid=grp.getnrnam(run_group)[2]
        if hasattr(os, 'setegid'):
            os.setegid(gid)
        #else?
    if run_user is not None:
        uid=pwd.getpwnam(run_user)[2]
        if hasattr(os, 'seteuid'):
            os.seteuid(uid)
        #else?

    loadServices()
    
    # revv 'er up
    _svr=Server(configFiles)
    _svr.mainloop()
    
__all__=['Server']    
