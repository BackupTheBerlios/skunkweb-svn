.. -*-rst-*-

PyDO2 Manual
~~~~~~~~~~~~

Introduction
------------


Acknowledgements
----------------


Defining Table Classes
----------------------

A PyDO class corresponds to a single database table and declares the
attributes of that table's columns by populating class attributes::

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


Projections
+++++++++++


Making Queries
--------------


`getSome()` and `getUnique()`
+++++++++++++++++++++++++++++


Operators
+++++++++






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

