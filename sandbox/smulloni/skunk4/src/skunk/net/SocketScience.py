#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
"""
"Takes some of the rocket science out of socket science."

Normally, calling the recv method on a socket object doesn't guarantee
that you'll get as many bytes as you ask for.  Because of this fact
(which is because UNIX works this way), this module makes it easy to
say, "I want X number of bytes in N seconds or bust."

"""

import socket

class ShortReadError(Exception): pass
class ShortWriteError(Exception): pass

class _default: pass

def read_up_to(sock, maxlength, timeout=_default):
    """
    Promises to read up to at most maxlength bytes from sock.

    If timeout is specified, the socket timeout is set to that value
    for the duration of the call, but is reset to whatever the
    original value is before the method returns.
    """
    dotimeout=timeout is not _default
    if dotimeout:
        originaltimeout=sock.gettimeout()
        sock.settimeout(timeout)
    try:
        dat=''
        while len(dat) < maxlength:
            rd=sock.recv(maxlength - len(dat))
            if len(rd)==0:
                break
            dat=dat+rd
        return dat
    finally:
        if dotimeout:
            sock.settimeout(originaltimeout)

def read_this_many(sock, length, timeout=_default):
    """
    Promises to read length bytes from sock, or bust with either a
    socket.error (including socket.timeout) or a ShortReadError, if we
    didn't get as many bytes as we expected.

    If timeout is specified, the socket timeout is set to that value
    for the duration of the call, but is reset to whatever the
    original value is before the method returns.
    
    """
    dotimeout=timeout is not _default
    if dotimeout:
        originaltimeout=sock.gettimeout()
        sock.settimeout(timeout)
    try:
        dat=''
        while len(dat) < length:
            rd=sock.recv(length - len(dat))
            if len(rd)==0:
                raise ShortReadError, \
                      "socket: got 0 bytes this read, %s total, wanted %s" % \
                      (len(dat), length)
            dat=dat+rd
        return dat
    finally:
        if dotimeout:
            sock.settimeout(originaltimeout)

def send_it_all(sock, s):
    """Promises to write all of s to the sock, or bust.  If we for some reason
    write 0 bytes at any time, we raise ShortWriteError because this usually
    indicates that the connection has died."""
    sentlen=0
    len_s=len(s)
    while sentlen < len_s:
        thislen=sock.send(s[sentlen:])
        if thislen == 0:
            raise ShortWriteError, \
                  "wrote 0 bytes this write, %s total, wanted %s" % \
                  (sentlen, len_s)
        sentlen=sentlen+thislen
    return sentlen


__all__=['ShortReadError',
         'ShortWriteError',
         'read_up_to',
         'read_this_many',
         'send_it_all']
