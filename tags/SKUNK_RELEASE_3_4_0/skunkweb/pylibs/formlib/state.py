######################################################################## 
#  Copyright (C) 2002 Jacob Smullyan <smulloni@smullyan.org>
#                     Drew Csillag <drew_csillag@yahoo.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
########################################################################

import base64
import cPickle
import md5

class InvalidStateException(Exception): pass

class InPageStateManager:
    """
    responsible for holding and marshalling into
    a value that can be placed securely in a hidden field
    some value.  The nonce is used to generate a verifiable
    hash.  If you want to further encrypt the pickled value
    of the state, use a stateEncryptor, which should have
    encrypt() and decrypt() methods (like the class in aesencrypt,
    or a rotor object). 
    """
    def __init__(self,
                 nonce,
                 stateEncryptor=None):
        self.stack = [] 
        self.state = {}
        self.nonce=nonce
        self.encryptor = stateEncryptor

    def write(self):
        s = cPickle.dumps((self.stack, self.state), 1)
        if self.encryptor:
            s = self.encryptor.encrypt(s)
        hash = md5.md5(self.nonce + s).digest()
        outv = base64.encodestring(hash + s)
        return ''.join(outv.split('\n'))

    def read(self, statestr):
        inv = base64.decodestring(statestr)
        hash, pick = inv[:16], inv[16:]
        nhash = md5.md5(self.nonce + pick).digest()
        if nhash != hash:
            raise InvalidStateException, 'state has been tampered with'
        if self.encryptor:
            pick = self.encryptor.decrypt(pick)
        (self.stack, self.state) = cPickle.loads(pick)

    def store_form(self, form):
        self.state.setdefault(form.name, {})
        self.state[form.name].update(form.getData())

    def push_formname(self, formname):
        self.stack.append(formname)

    def pop_formname(self):
        return self.stack.pop()

    def peek_formname(self):
        if self.stack:
            return self.stack[-1]

    def clear(self):
        self.state.clear()
        self.stack=[]
        
__all__=['InvalidStateException', 'InPageStateManager']
