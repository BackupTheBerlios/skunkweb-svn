# Time-stamp: <02/11/20 12:11:39 smulloni>
# $Id: aesencrypt.py,v 1.1 2002/11/20 17:34:11 smulloni Exp $
"""
a convenience class for encrypting strings or
arbitrary length using AES.  Requires PyCrypto,
available at from http://www.amk.ca/python/code/crypto.html.
"""
import Crypto.Cipher.AES as AES
import md5


class AESEncryptor:
    def __init__(self, key, IV=None):
        self.key=key
        self.__key=md5.md5(key).digest()
        if IV==None:
            IV=self.key[:16].ljust(16)
        self.IV=IV

    def _pad(self, thing):
        s='%dX%s' % (len(thing), thing)
        ls=len(s)
        m=ls % AES.block_size
        return s.ljust(ls-m + AES.block_size)

    def _unpad(self, padded):
        xind=padded.find('X')
        num=int(padded[:xind])
        return padded[xind+1:xind+1+num]

    def encrypt(self, thing):
        thing=self._pad(thing)
        return AES.new(self.__key, AES.MODE_CBC, self.IV).encrypt(thing)

    def decrypt(self, encrypted):
        thing=AES.new(self.__key, AES.MODE_CBC, self.IV).decrypt(encrypted)
        return self._unpad(thing)
