
PyDO2 Manual
~~~~~~~~~~~~

Introduction
------------

PyDO is an ORM (Object-Relational Mapper) database access library for
Python.  This document describes PyDO version 2.0 and later only.

Acknowledgements
----------------

PyDO was originally written by Drew Csillag in 2000, and released
under the GPL license in 2001 as part of SkunkWeb.  Several developers
have contributed to the codebase since then (see ACKNOWLEDGEMENTS in
the source distribution).  Jacob Smullyan is responsible for work on
the 2.0 series, but while errors and misfeatures are attributable to
him, the fundamental design remains Csillag's.

Overview
--------

    *Note*: PyDO is a Python package, but all the public objects
    within its submodules (with the exception of the drivers) are
    imported into its top-level namespace.  In what follows we will
    assume that the current namespace has been initialized by::

       from PyDO import *

    (In particular, this means that when we want to refer to the
    ``PyDO.PyDO`` class, we shall just write ``PyDO``.)

PyDO's basic strategy is to let you define a ``PyDO`` subclass for
every table in a database that you wish to represent.  Each instance
of a PyDO class contains the data for one row in a database table. As
``PyDO`` is a ``dict`` subclass, you can access this data by key, or,
if the class attribute ``use_attributes`` is true (the default) by
attribute.  In either case, the key or attribute name is the name of
the database column::

   >>> MyPyDOInstance.title
   'Fustian Wonders'
   >>> MyPyDOInstance['title']
   'Fustian Wonders'

If you have column names that are Python keywords (such as "pass",
"class", etc.)  a warning will be raised when the class is defined and
an attempt at attribute access of that field will give rise to a
SyntaxError, but you'll still be able to access it dictionary-style.

Instances are obtained, not by directly invoking the PyDO class's
constructor, but by calling one of various class methods, discussed
below, that return single instances or lists thereof.

If the class is declared mutable and has a unique constraint, it is
possible to mutate it by calling::

    MyInstance.fieldname=newValue

or, equivalently::

    MyInstance['fieldname']=newValue

Multiple updates can be done together via ``update()``::

    MyInstance.update(dict(fieldname=newValue,
                           otherFieldname=otherValue))

If you attempt to mutate an immutable PyDO instance, a ``PyDOError``
will be raised.


Defining Table Classes
----------------------

To create a database access api for a database using PyDO, you define
a subclasses of ``PyDO``, each corresponding to a single database
table and declaring the attributes of that table's columns by
populating class attributes::

  from PyDO import PyDO, Sequence, Unique

  class Article(PyDO):
      """PyDO class for the Article table"""

      # define a connection alias so that PyDO knows how to 
      # connect to the database
      connectionAlias='my_db'

      # the table name
      table='article'

      # whether we are allowed to update instances of this class;
      # this defaults to True anyway.
      mutable=True

      # declare the fields
      fields=(Sequence('id'),
              Unique('title'),
              'slug',
              'author',
              'created',
              'body')

The ``connectionAlias`` attribute must correspond to an alias
initialized elsewhere that tells PyDO how to create a database
connection.

The ``table`` attribute is simply the name of the table, view, or
table-like entity (set function, for instance).  If the database
supports schemas, like later version of postgresql, the schema name
can be included here, if desired (e.g., ``myschema.mytable``).

The ``fields`` attribute should be a tuple or list of either
``PyDO.Field`` instances (of which ``Sequence`` and ``Unique`` are
subclasses), strings (which should be column names), or tuples that
can be passed to the ``PyDO.Field`` constructor (i.e.,
``PyDO.Field(**fieldTuple)``).   

A ``Sequence`` field is used to represent either an auto-increment
column, for databases like MySQL that use that mechanism, or a
sequence column, as used in PostgreSQL.  These columns are implicitly
unique.  A ``Unique`` field is used to represent a column that has a
single-column unique constraint.  Multiple-column unique constraints
can also be indicated, with the ``unique`` class attribute::

   from PyDO import PyDO
 
   class ArticleKeywordJunction(PyDO):
   """PyDO class for junction table between Article and Keyword"""
       connectionAlias="my_db"
       table="article_keyword_junction"
       fields=('article_id',
               'keyword_id')
       unique=(('article_id', 'keyword_id'),)

It is not necessary to declare any unique constraints in a ``PyDO``
class.  However, if your table has no unique constraints, an instance
of the corresponding ``PyDO`` class won't be able to identify the
unique row in the database to which it corresponds, and hence will not
be mutable.  (If the class is mutable, however, it will still be
possible to perform inserts and mass updates and deletes.)


Inheritance Semantics
+++++++++++++++++++++

PyDO classes are normal Python classes which use a metaclass to parse
the ``field`` and ``unique`` class attribute declarations and store
the derived information in private fields (currently ``_fields``,
``_unique``, and ``_sequenced``, but that is subject to
reimplementation).  This private fields have special inheritance
semantics, in that fields, and their associated unique/sequenced
properties, are inherited from superclasses even if they are not
declared in the subclass.  (This behavior is applicable not only to
PostgreSQL table inheritance, but to defining base or mixin classes,
which need not be PyDO subclasses themselves, that define groups of
fields that are shared by multiple tables.)

Projections
+++++++++++

An exception is made to the default inheritance behavior -- that
subclasses inherit their superclasses' fields -- for the case of
projection subclasses, in which fields are not inherited.  Projections
are useful when you wish to select only a few columns of a larger
table.  To derive a projection from a PyDO class, simply call the
class method ``project()`` on the class, passing in a tuple of fields
that you wish to include in the projection::

   myProjection=MyBaseClass.project(('id', 'title'))

The return value is a new PyDO class. This class is cached, so if you
call ``project()`` again with the same arguments you'll get a
reference to the same class.

Making Queries: ``getSome()`` and ``getUnique()``
-------------------------------------------------

There are two class methods provided for performing SELECTs.
``getSome`` returns a list of rows of ``PyDO`` instances::

   >>> myFungi.getSome()
  [{'id' : 1, 'species' : 'Agaricus lilaceps', 'comment' : 'nice shroom!'}, 
   {'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' : None}]

``getUnique`` returns a single instance.  You must provide enough
information to getUnique to satisfy an unique constraint; this is
accomplished by passing in keyword parameters where the keywords are
column names corresponding to the columns of a unique constraint
declared for the object, and the values are what you are asserting
those columns equal::

  >>> myFungi.getUnique(id=2)
  {'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' : None}
  >>> myFungi.getUnique(id=55) is None
  True
  
Assuming that ``comment`` is not a unique field above, you could not
add selection criteria based on ``comment`` to ``getUnique()``, but
could to ``getSome``::

 >>> myFungi.getSome(comment=None)
 [{'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' :  None}]
 >>> myFungi.getSome(comment='better than asparagus', id=55)
 []
                

Operators
+++++++++

In addition to specifying selection criteria by keyword argument, PyDO
gives you three other ways:

  1. If you supply a string as the first argument to ``getSome()``, it
     will be placed as-is in a WHERE clause.  Remaining positional
     arguments will be taken to be values for bind variables in the
     string::

         >>> myFungi.getSome("comment != %s", None)

     If you use bind variables, the paramstyle you use must be the
     same as that of the underlying Python DBAPI driver.  To support
     the ``pyformat`` and ``named`` paramstyles, in which variables
     are passed in a dictionary, you can pass in a dictionary as the
     second argument.  When using this style with ``getSome()``, you
     cannot use keyword arguments to express column equivalence.

  2. You can use ``SQLOperator``s::
       
       >>> myFungi.getSome(OR(EQ(FIELD('comment'), 'has pincers'),
       ...                    LT(FIELD('id'), 40),
       ...                    LIKE(FIELD('species'), '%micromega%')))
       [{'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' :  None}]

  3. You can use tuples that are turned into ``SQLOperator``s for you;
     this is equivalent to the above::

       >>> myFungi.getSome(('OR', 
       ...                  ('=', FIELD('comment'), 'has pincers'),
       ...                  ('<', FIELD('id'), 40),
       ...                  ('LIKE', FIELD('species', '%micromega%'))))
       [{'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' :  None}]

Either operator syntax can be mixed freely with keyword arguments to
express column equivalence.

The basic idea of operators is that they renotate SQL in a prefix
rather than infix syntax, which may not be to everyone's taste; you
don't need to use them, as they are purely syntactical sugar.  

Order, Offset and Limit
+++++++++++++++++++++++



Inserts, Updates, and Deletes
-----------------------------


Joins
-----


Connection Parameters
---------------------


Caveats
-------


A Complete Example
------------------





..
   Local Variables:
   mode: rst
   indent-tabs-mode: nil
   sentence-end-double-space: t
   fill-column: 70
   End:
