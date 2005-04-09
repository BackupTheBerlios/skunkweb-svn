from skunk.net.server.socketmgr import SocketManager
from skunk.web.config import Configuration, updateConfig, mergeDefaults

"""

do I continue to use hooks?  If so, I need to add ServerStart and ChildStart.

Also, I don't like the way logging is done.  It doesn't make sense
that the server's logger is stored in "Configuration.logger". This
isn't really a configuration setting at all; it should be controlled
by subclassing.  So I'd pull it completely out of configuration.

Bootstrap does need a spot to configure the logging.  A separate log
file, I suppose.

"""

class Server(SocketManager):
    """ the skunkweb server itself."""
    def __init__(self):
        super(Server, self).__init__(Configuration.pidFile,
                                     Configuration)


__all__=['Server']    
