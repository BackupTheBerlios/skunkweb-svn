"""
A static process manager (no grow/shrink) that can handle reloads.
Derive from the ProcessManager class to do it.

Used currently by SkunkWeb to handle management of the child processes
and server restart.  If children die, it will create new children to
take their place.

If you want to write a multi-process, static number of kids (until
reload anyway) server, this is for you.

TODO:
   * review reload
   * optionally permit grow/shrink, IPC, so that this is a general
     purpose pre-forking manager (??)
     
"""

import copy
import grp
import logging
import os
import pwd
import signal
import sys
import time

class SignalException(Exception):
    def __init__(self, *msg):
        Exception.__init__(self, 'signal caught: %s' \
                           % self.__class__.sig_name)

class TermSignal(SignalException):
    sig_name='SIGTERM'

class HupSignal(SignalException):
    sig_name='SIGHUP'

class bag(object):
    def __init__(self, **kw):
        self.__dict__=kw
    
class ProcessManager(object):
    """a fixed, preforking process manager"""

    _defaults=dict(numProcs=5,
                   maxKillTime=5,
                   pollPeriod=5,
                   logger=logging.getLogger('skunk.net.server'),
                   foreground=False,
                   run_user=None,
                   run_group=None)

    def __init__(self,
                 pidFile,
                 config=None,
                 **kw):
        """create a ProcessManager with the given pidFile path and config object.
        The config object must be something with the attributes given in _defaults.
        """
        self.pidFile=pidFile
        if config is None:
            config=bag(**kw)
        self.config=config
        self._initAttrs()
        self._children = {}

        # catch sigchild and reap kids (mainly to interrupt a sleep() call)
        signal.signal(signal.SIGCHLD, self._SIGCHLDHandler)

        # handle these signals to propagate them
        signal.signal(signal.SIGHUP, self._SIGHUPHandler)
        signal.signal(signal.SIGTERM, self._SIGTERMHandler)

        self._sig = None

        # get a module snapshot.
        self.moduleSnapshot()

    def _initAttrs(self):
        # sync instance attributes with config object and defaults
        for k, v in self._defaults.iteritems():
            # some values in the defaults may be mutable, so use
            # copy.copy
            setattr(self, k, getattr(self.config, k, copy.copy(v)))

    # logging methods
    def log(self, level, *args, **kwargs):
        self.logger.log(level, *args, **kwargs)

    def debug(self, *args, **kwargs):
        self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)

    def warn(self, *args, **kwargs):
        self.logger.warn(*args, **kwargs)

    def critical(self, *args, **kwargs):
        self.logger.critical(*args, **kwargs)

    def error(self, *args, **kwargs):
        self.logger.error(*args, **kwargs)

    def exception(self, *args, **kwargs):
        self.logger.exception(*args, **kwargs)


    def _SIGCHLDHandler(self, *args):
        pass

    def _SIGHUPHandler(self, *args):
        self._sig = "SIGHUP"
            
    def _SIGTERMHandler(self, *args):
        self._sig = "SIGTERM"

    def moduleSnapshot(self):
        """
        Take a snapshot of modules that need to stick through inits()
        """
        self._modules = sys.modules.keys()
        self._modules.sort()

    def periodic(self):
        """
        override this method if you want to do something in the parent
        process periodically
        """
        pass

    def init(self):
        """override this method to do something before the server starts
        """
        pass

    def run(self):
        """override this method to actually do something in the child
        process
        """
        raise NotImplementedError, 'run method not overridden'

    def _run_as(self):
        if self.run_group:
            gid=grp.getgrnam(self.run_group)[2]
            os.setgid(gid)
        if self.run_user:
            uid=pwd.getpwnam(self.run_user)[2]
            euid=os.getuid()
            try:
                os.seteuid(euid)
            except AttributeError:
                pass
            os.setuid(uid)
        self.run()

    def mainloop(self):
        """the method used to actually fire off the server"""
        self.init()
        if self.numProcs == 1:
            self.info('running in non-daemon mode with single process')
            self._run_as()
            sys.exit()

        # suppress going to background (for running under daemontools)
        if not self.foreground:
           # become daemon and process group leader
           self.info("daemonizing...")
           if os.fork():
               sys.exit()
           if os.fork():
               sys.exit()
           os.setsid()
        else:
           self.info('not going to background')

        #write the pid file
        open(self.pidFile,'w').write('%s' % os.getpid())

        while 1:
            try:
                # do any periodic tasks
                self.periodic()

                # reap any process corpses
                self._reap()

                # if are we short of procs, spawn some new ones
                if len(self._children) < self.numProcs:
                    self._spawn()

                # wait, we'll be interrupted by SIGCHLD if anything
                # important happens
                try:
                    time.sleep(self.pollPeriod)
                except:
                    pass
                
                # deal with signals
                if self._sig == 'SIGTERM': raise TermSignal 
                if self._sig == 'SIGHUP': raise HupSignal
                
            except (TermSignal, KeyboardInterrupt):
                # server shutdown
                self.info('shutting down')
                self._die()
                self.stop()
                try:
                    os.unlink(self.pidFile)
                except:
                    self.exception('could not unlink pid file!')
                self.info('server shut down')
                sys.exit()

            except HupSignal:
                # nice restart
                self.info('restarting')
                # kill off children
                self._die()
                # reload modules
                self.reload()
                # reload configuration
                self._initAttrs()
                self._sig = None
                self.init()

    def _reap(self):
        while 1:
            try:
                pid, exitStatus = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                self.info('child, pid %d died status %s',
                         pid,
                         exitStatus)
                del self._children[pid]
            except:
                break

    def _spawn(self):
        # precondition: len(self._children) < self.numProcs
        numToSpawn = self.numProcs - len(self._children)
        assert numToSpawn > 0
        self.info('spawning %d child(ren)', numToSpawn)
        for i in xrange(numToSpawn):
            self.debug('spawning child')
            kidPid = os.fork()
            if not kidPid:
                # we're the kid.  Set the signal handlers to their
                # normal bit
                signal.signal(signal.SIGCHLD, signal.SIG_DFL)
                signal.signal(signal.SIGHUP, signal.SIG_DFL)
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                self._run_as()
                sys.exit()
            self._children[kidPid] = 1

    def _die(self):
        curTime = time.time()

        # nuke all processes
        self.info('killing all children with TERM')
        for pid in self._children.keys():
            os.kill(pid, signal.SIGTERM)
            
        # wait for them to die
        while len(self._children):
            try:
                time.sleep(1)
            except:
                pass
            self._reap()
            if time.time() - curTime > self.maxKillTime:
                break

        if len(self._children):
            # grrr, they're still there! Kill them hard
            self.info('killing remaining children with KILL')
            for pid in self._children:
                os.kill(pid, signal.SIGKILL)

        # now wait for them to die
        while len(self._children):
            try:
                time.sleep(1)
            except:
                pass
            self._reap()

    def reload(self):
        """override this method to handle reload events.
        You probably want to call your superclass first!, then do
        what you must.
        """
        
        # Just reload ALL the modules but the ones we keep 
        for m in sys.modules.iterkeys():
            if m not in self._modules:
                if sys.modules[m]:
                    mm = sys.modules[m]
                    bits = m.split('.')
                    if len(bits) > 1:
                        # module is part of a package
                        parent = '.'.join(bits[:-1])
                        if sys.modules.has_key(parent):
                            pmod = sys.modules[parent]
                            if (hasattr(parent, bits[-1])
                                and id(getattr(parent, bits[-1])) == id(mm)):
                                # delete module from parent package
                                delattr(parent, bits[-1])
                    # Not None, tear down its dictionary
                    mm.__dict__.clear()
                del sys.modules[m]

        

    def stop(self):
        """override this to be called when the server is shut down
        """
        pass


__all__=['ProcessManager']
