# Time-stamp: <03/02/08 19:49:54 smulloni>
# $Id: FSSessionStore.py,v 1.4 2003/05/01 20:45:54 drew_csillag Exp $

#  Copyright (C) 2001 Jacob Smullyan <smulloni@smullyan.org>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
# $Author: drew_csillag $
# $Revision: 1.4 $
########################################################################


import cPickle
import fcntl
import os
import time
from SkunkExcept import SkunkStandardError
from SkunkWeb import Configuration
from SkunkWeb.LogObj import DEBUG, logException
from SkunkWeb.ServiceRegistry import SESSIONHANDLER
from sessionHandler.Session import SessionStore

_sesspath=Configuration.SessionHandler_FSSessionDir

class FSSessionStoreImpl(SessionStore):
    """
    a SessionStore implementation that stores session pickles in files, one per session.
    Can only be used for standalone servers or in load-balancing setups where distributed
    sessions aren't necessary (which, given the fixed size of the SkunkWeb pool, is probably
    not a good fit).
    """ 
    _lastReaped=int(time.time())    
    
    def __init__(self, id):
        self.id=id        
        self.__picklepath=os.path.join(_sesspath, 
                                       id)
        # if the session dir doesn't exist, try to create it
        if not os.path.exists(_sesspath):
            try:
                os.makedirs(_sesspath)
            except:
                ERROR("FSSessionStoreImpl needs writeable session directory %s" % _sesspath)
                raise
        if not os.access(_sesspath, os.W_OK):
            raise SkunkStandardError, "FSSessionStoreImpl needs writeable session directory %s" % _sesspath
         
    def load(self):
        self._checkReap()
        return self.__getPickle() or {}

    def __getPickle(self):
        if os.path.exists(self.__picklepath):
            f=open(self.__picklepath)
            fd=f.fileno()
            # let reads coexist
            fcntl.flock(fd, fcntl.LOCK_SH)
            try:
                data=cPickle.load(f)
            except:
                logException()
                data={}
            fcntl.flock(fd, fcntl.LOCK_UN)
            f.close()
            return data
    
    def save(self, data):
        self.__setPickle(data)
        self._checkReap()

    def __setPickle(self, data):
        f=open(self.__picklepath, 'w')
        fd=f.fileno()
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            cPickle.dump(data, f, 1)
        except:
            logException()
        fcntl.flock(fd, fcntl.LOCK_UN)
        f.close()
        
    def _checkReap(self):
        DEBUG(SESSIONHANDLER, "in _checkReap")
        reapInterval=Configuration.SessionReapInterval
        DEBUG(SESSIONHANDLER, "reap interval is %d" % reapInterval)
        DEBUG(SESSIONHANDLER, "last reaped: %d" % self.lastReaped())
        if reapInterval>0:
            currentTime=int(time.time())
            if currentTime>=(self.lastReaped() + reapInterval):
                self.reapOldRecords()
                self.lastReaped(currentTime)

    def reapOldRecords(self):
        # walk through contents of session directory and delete any
        # lapsed files
        now=time.time()
        for f in os.listdir(_sesspath):
            p=os.path.join(_sesspath, f)
            lastAccess=os.path.getatime(p)
            if now-lastAccess>Configuration.SessionTimeout:
                os.remove(p)

    def lastReaped(self, newVal=None):
        if not newVal:
            return FSSessionStoreImpl._lastReaped
        else:
            FSSessionStoreImpl._lastReaped=newVal
                
    def delete(self):
        os.remove(self.__picklepath)
        
    def touch(self):
        curtime=time.time()
        os.utime(self.__picklepath, (curtime, curtime))

########################################################################
# $Log: FSSessionStore.py,v $
# Revision 1.4  2003/05/01 20:45:54  drew_csillag
# Changed license text
#
# Revision 1.3  2003/02/09 00:58:37  smulloni
# fix for Spruce Weber's hang w/ pickle error
#
# Revision 1.2  2002/02/05 18:58:19  smulloni
# fixed bug (thanks to Spruce Weber): was referring to "os.join" (ugh)
#
# Revision 1.1  2001/08/06 17:16:04  smulloni
# adding session store that uses pickle files in the local filesystem.
#
########################################################################
