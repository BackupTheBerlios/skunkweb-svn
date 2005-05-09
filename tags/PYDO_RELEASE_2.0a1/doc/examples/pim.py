"""
a small example PIM application, using sqlite
"""
import os
from mx.DateTime import now
from PyDO2 import *



class Contact(PyDO):
    connectionAlias='pim'
    table='contact'
    fields=(Sequence('id'),
            'first_name',
            'last_name',
            'address_id1',
            'address_id2',
            'email1',
            'email2',
            'work_phone',
            'home_phone',
            'mobile_phone')

    def getAddress1(self):
        if self.address_id1 is not None:
            return Address.getUnique(id=self.address_id1)

    def getAddress2(self):
        if self.address_id2 is not None:
            return Address.getUnique(id=self.address_id2)

    def addNote(self, title, body):
        n=Note.new(refetch=1, title=title, body=body, created=now())
        junction=ContactNote.new(contact_id=self.id,
                                 note_id=n.id)
        

    def getNotes(self):
        return self.joinTable('id',
                              'contact_note',
                              'contact_id',
                              'note_id',
                              Note,
                              'id')

class Address(PyDO):
    connectionAlias='pim'
    table='address'
    fields=(Sequence('id'),
            'line1',
            'line2',
            'town',
            'state',
            'country',
            'postal_code')

    def getContacts(self):
        return Contact.getSome(OR(EQ(FIELD('address_id1'), self.id),
                                  EQ(FIELD('address_id2'), self.id)))

class Note(PyDO):
    connectionAlias="pim"
    table="note"
    fields=(Sequence('id'),
            'title',
            'body',
            'created')

class ContactNote(PyDO):
    connectionAlias='pim'
    table="contact_note"
    fields=('contact_id',
            'note_id')
    unique=(('contact_id',
             'note_id'),)

DB=os.environ.get('PIMDB', 'pim.db')
initAlias('pim', 'sqlite', DB)

def initDB():
    joseAddress=Address.new(refetch=1,
                            line1="43 Chestnut Place",
                            line2="Fourth Floor",
                            town="Princeton",
                            state="NJ",
                            country="USA",
                            postal_code="06540")
    jose=Contact.new(refetch=1,
                     first_name='Jose',
                     last_name='Gutenberg',
                     email1='jgutenberg@example.com',
                     address_id1=joseAddress.id,
                     home_phone='609/555-1234')
    jose.addNote('French Tutor',
                 'meet every other Thursday at 7pm in the Annex')
    jose.commit()
    
                     
