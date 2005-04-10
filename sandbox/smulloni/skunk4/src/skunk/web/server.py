
import grp
import os
import pwd
import sys

from skunk.net.server.socketmgr import SocketManager
from skunk.web.config import Configuration, loadConfig, updateConfig, mergeDefaults


"""

Actually, ServerStart happens early, when the services are loaded.
For that reason I don't think it is necessary.  Services will have
another service initialization hook.  (If so -- we must call it again
when the server is HUPed., which suggests that it should be
implemented as part of the Server class, not outside it.)

Bootstrap does need a spot to configure the logging.  A separate conf
file, I suppose.

"""

class Server(SocketManager):
    """ the skunkweb server itself."""
    def __init__(self):
        super(Server, self).__init__(Configuration.pidFile,
                                     Configuration)
    def run(self):
        ChildStart()
        super(Server, self).run()

def configDefaults():
    Configuration.mergeDefaults(run_group=None,
                                run_user=None,
                                services=(),
                                jobs=())

    
_svr=None

def init(*configFiles):
    global _svr
    if _svr:
        raise RuntimeError, "already initialized"
    # configure logging -- TBD
    
    # load configuration
    loadConfig(*configFiles)
    configDefaults()

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
    # load services
    for servicename in Configuration.services:
        __import__(servicename)
        mod=sys.modules[servicename]
        if hasattr(mod, 'serviceInit'):
            mod.serviceInit()

    # revv 'er up
    _svr=Server()
    _svr.mainloop()
    
__all__=['Server']    
