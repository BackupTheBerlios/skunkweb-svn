PyDO2 Manual
~~~~~~~~~~~~

:Author: Jacob Smullyan <smulloni@smullyan.org>
:Version: 0.1
:Status: Draft

.. contents:: Table of Contents
.. section-numbering::


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

.. Note::  PyDO is a Python package, but all the public objects
    within its submodules (with the exception of the drivers) are
    imported into its top-level namespace.  In what follows we will
    assume that the current namespace has been initialized by::

       from PyDO import *

    (In particular, this means that when we want to refer to the
    ``PyDO.PyDO`` class, we shall just write ``PyDO``.)

PyDO's basic strategy is to let you define a ``PyDO`` subclass for
every table in a database that you wish to represent.  Each ``PyDO``
instance contains the data for one row in a database table. As
``PyDO`` is a ``dict`` subclass, you can access this data by key, and,
if the class attribute ``use_attributes`` is true (the default) also
by attribute.  In either case, the key or attribute name is the name
of the database column::

   >>> MyPyDOInstance.title
   'Fustian Wonders'
   >>> MyPyDOInstance['title']
   'Fustian Wonders'

If you have column names that are Python keywords (such as "pass",
"class", etc.)  a warning will be raised when the class is defined and
an attempt at attribute access of that field will give rise to a
``SyntaxError``, but you'll still be able to access it
dictionary-style.

Instances are obtained, not by directly invoking the PyDO class's
constructor, but by calling one of various class methods, discussed
below, that return single instances or lists thereof.


Defining Table Classes
----------------------

To model a database table, you define a subclass of ``PyDO`` and set
some class attributes that describe the table::

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
supports schemas, like later version of PostgreSQL, the schema name
can be included here, if desired (e.g., ``myschema.mytable``).

The ``fields`` attribute should be a tuple or list of either ``Field``
instances (of which ``Sequence`` and ``Unique`` are subclasses),
strings (which should be column names), or tuples that can be passed
to the ``Field`` constructor (i.e., ``Field(**fieldTuple)``).  You can
also use your own ``Field`` subclasses if you wish to store additional
information about fields (e.g., data type, validators, etc.).

A ``Sequence`` field is used to represent either an auto-increment
column, for databases like MySQL that use that mechanism, or a
sequence column, as used in PostgreSQL.  These columns are implicitly
unique.  A ``Unique`` field is used to represent a column that has a
single-column uniqueness constraint.  Multiple-column uniqueness
constraints can also be indicated, with the ``unique`` class
attribute::

   from PyDO import PyDO
 
   class ArticleKeywordJunction(PyDO):
   """PyDO class for junction table between Article and Keyword"""
       connectionAlias="my_db"
       table="article_keyword_junction"
       fields=('article_id',
               'keyword_id')
       unique=(('article_id', 'keyword_id'),)

The ``unique`` attribute can be thought of as analogous to how, in
SQL, you may declare uniqueness constraints in a separate clause after
you have declared the fields; it is optional to do so for
single-column uniqueness constraints, which are more conveniently
declared inline with the field, but necessary for the multi-column
case.  

It is not necessary to declare any uniqueness constraints in a
``PyDO`` class at all, either implicitly with the ``Unique`` field
class, or via the ``unique`` class attribute.  However, if you do not,
instances of the corresponding ``PyDO`` class won't be able to
identify the unique rows in the database table to which they
correspond, and hence the instances will not be mutable.  (If the
class is mutable, however, it will still be possible to perform
inserts and mass updates and deletes.)

The inherited fields, uniqueness constraints, and sequences of a class
may be read, but not changed, through the class methods
``getFields()``, ``getUniquenessConstraints()``, and
``getSequences()``, respectively.


Inheritance Semantics
+++++++++++++++++++++

``PyDO`` classes are normal Python classes (subclassing ``dict``)
which use a metaclass to parse the ``field`` and ``unique`` class
attribute declarations and store the derived information in private
fields.  Special inheritance semantics obtain for ``field`` and
``unique``, in that the privately stored parsed values corresponding
to those declarations are inherited from superclasses even if
``fields`` is redeclared in the subclass, shadowing any superclass's
declaration.  Subclasses therefore may augment the field listing of
their base classes.  This behavior is applicable not only to
PostgreSQL table inheritance, but to defining base or mixin classes
(which need not be ``PyDO`` subclasses themselves) that define groups
of fields that are shared by multiple tables.  

Normally, if a subclasses redeclares a field declared by a base class,
the subclass's declaration overrides that of the base class, but an
exception is made for declarations that simply state the fieldname as
a string; in that case, any previous, more informative declaration
will be inherited.

.. warning::
    This is generally useful (in the case of projections particularly
    --see below) but if you wished to override a superclass's
    definition, say, of ``Unique('species')``, just to the non-unique
    ``Field('species')``, you would have to explicitly use the
    ``Field`` constructor rather than simply ``'species'``.


Projections
+++++++++++

An exception is made to the default inheritance behavior -- that
subclasses augment, rather than shadow, their superclasses' field
listing -- for the case of projection subclasses, in which the local
declaration of fields overrides that of superclasses.  Projections are
useful when you wish to select only a few columns from a larger table.
To derive a projection from a ``PyDO`` class, simply call the class
method ``project()`` on the class, passing in a tuple of fields that
you wish to include in the projection::

   myProjection=MyBaseClass.project(('id', 'title'))

The return value is a subclass of ``myBaseClass`` with the fields
``id`` and ``title``. This class is cached, so if you call
``project()`` again with the same arguments you'll get a reference to
the same class.

Because of the special inheritance semantics for simple string field
declarations, if ``MyBaseClass`` in the above example is defined as
follows::

   class myBaseClass(PyDO):
       fields=(Sequenced('id'),
               Unique('title'),
               'author'
               'ISBN',
               'first_chapter')

``myProjection`` will still know that ``id`` and ``title`` are unique,
and that ``id`` is sequenced.


Making Queries: ``getSome()`` and ``getUnique()``
-------------------------------------------------

There are two class methods provided for performing SELECTs.
``getSome`` returns a list of rows of ``PyDO`` instances::

   >>> myFungi.getSome()
  [{'id' : 1, 'species' : 'Agaricus lilaceps', 'comment' : 'nice shroom!'}, 
   {'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' : None}]

``getUnique`` returns a single instance.  You must provide enough
information to ``getUnique`` to satisfy precisely one declared
uniqueness constraint; this is accomplished by passing in keyword
parameters where the keywords are column names corresponding to the
columns of a uniqueness constraint declared for the object, and the
values are what you are asserting those columns equal for the unique
row::

  >>> myFungi.getUnique(id=2)
  {'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' : None}
  >>> myFungi.getUnique(id=55) is None
  True 
  
``getSome`` is similar, but admits a much wider range of query
options, and returns a list of ``PyDO`` instances.  Assuming that
``comment`` is not a unique field above, you could not add selection
criteria based on ``comment`` to ``getUnique()``, but could to
``getSome``::

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

2. You can use ``SQLOperator`` instances::
       
     >>> myFungi.getSome(OR(EQ(FIELD('comment'), 'has pincers'),
     ...                    LT(FIELD('id'), 40),
     ...                    LIKE(FIELD('species'), '%micromega%')))
     [{'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' :  None}]

3. You can use tuples that are turned into ``SQLOperator`` instances
   for you; this is equivalent to the above::

     >>> myFungi.getSome(('OR', 
     ...                  ('=', FIELD('comment'), 'has pincers'),
     ...                  ('<', FIELD('id'), 40),
     ...                  ('LIKE', FIELD('species', '%micromega%'))))
     [{'id' : 2, 'species' :  'Agaricus micromegathus', 'comment' :  None}]

Either operator syntax can be mixed freely with each other and with
keyword arguments to express column equivalence.

The basic idea of operators is that they renotate SQL in a prefix
rather than infix syntax, which may not be to everyone's taste; you
don't need to use them, as they are purely syntactical sugar.  One
convenient thing about them is that they automatically convert values
included in them to bind variables in the style of the underlying
DBAPI driver.

To represent an unquoted value, like a fieldname, a constant, or a
function, use the ``FIELD`` or ``CONSTANT`` classes (actually, they
are synonyms).  Another helper class is ``SET``, for use with the
``IN`` operator::

    >>> myFungi.getSome(IN(FIELD('comment'), 
    ...                    SET('nice shroom!', 'has pincers')))


Order, Limit and Offset
+++++++++++++++++++++++

``getSome()`` accepts three additional keyword arguments:

  order 
      a fieldname to order by, with optional ' ASC' or ' DESC'
      suffix, or a tuple of such fieldname-with-optional-suffix
      strings. 
  offset
      an integer 
  limit 
      an integer


Refreshing An Instance
++++++++++++++++++++++

If you have reason to believe that the data you have for an object is
inaccurate or out of date, you can refresh it by calling
``myObj.refresh()``, as long as the object has uniqueness constraints
so it is possible to get the unique row to which it corresponds.


Inserts, Updates, and Deletes
-----------------------------

To insert a new record in the database and create the corresponding
``PyDO`` object, use the class method ``new()``::

   >>> subscription=Subscriptions.new(email='alvin@krinst.org',
                                      magazine='NYRB')
   >>> subscription
   {'email' : 'alvin@krinst.org', 'magazine' : 'NYRB'}

If the object has a field which will acquire a default non-null value
even though you haven't specified a value for it, PyDO will refetch it
for you of you pass the additional keyword argument ``refetch`` with a
true value::

   >>> poem=Sonnet.new(refetch=True,
                       title='Anguished Parsnips',
                       body='\n'.join(' '.join(['oy veh!' * 5]) * 14))
   >>> poem.id
   456740

This is equivalent to calling ``refresh()`` after ``new()``, and also
requires that a uniqueness constraint be been declared for the class.

If a class is declared mutable and has a uniqueness constraint, it is
possible to mutate an undeleted instance of it by calling::

    >>> poem['title']='Sayings of the Robo-Rabbi'

or, equivalently, if ``use_attributes`` is true for the class::

    >>> poem.title='Sayings of the Robo-Rabbi'

Multiple updates can be done together via ``update()``::

    MyInstance.update(dict(fieldname=newValue,
                           otherFieldname=otherValue))

Each mutation will cause an UPDATE statement to be executed on the
underlying database. If you attempt to mutate an immutable ``PyDO``
instance, a ``PyDOError`` will be raised.

It is also possible to update potentially many rows at once with the
class method ``updateSome()``::

   >>> Article.updateSome(dict(slug="nonsense"), 
   ...                    LT(FIELD("created"),
   ...                       CONSTANT("CURRENT_TIMESTAMP")),
   ...                    author='Smullyan')
   6
  
The first argument to ``updateSome()`` is a dictionary of values to
set for affected rows; remains positional and keyword args accept the
same arguments as ``getSome()`` (with the exception of ``order``,
``limit``, and ``offset`` which wouldn't make sense in this context).
The return value is the number of affected rows.

To delete an instance, call the instance method ``delete()``::

  >>> Article.getUnique(id=44).delete()

The method returns nothing; the instance in question is marked as
immutable.

To delete many rows at once, use the class method ``deleteSome()``::

  >>> Article.deleteSome(LT(FIELD("created"), 
  ...                       CONSTANT("CURRENT_TIMESTAMP")),
  ...                    author="Grisby Holloway")

The parameters accepted are again the same as for ``getSome())``,
except for ``order``, ``limit``, and ``offset``, and the return value
is the number of affected rows.


Joins
-----

Representing Joins Between Tables
+++++++++++++++++++++++++++++++++

To represent a one-to-one join between classes ``A`` and ``B``, add an
instance method to class ``A`` that calls ``B.getUnique()``::

    def getB(self):
        return B.getUnique(id=self.b_id)

To represent a one-to-many join, do the same, but with
``B.getSome()``::

    def getBs(self):
        return B.getSome(a_id=self.id)

To represent a many-to-many join between ``A`` and ``B`` through
junction table ``J``, add an instance method that calls
``joinTable()``::

    def getBs(self):
        return self.joinTable('id', 'J', 'a_id', 'b_id', B, 'id')

``joinTable()`` takes the following arguments:

``thisAttrNames``
    attribute(s) in current object to join from 
``pivotTable``
    pivot table name 
``thisSideColumns``
    column(s) that correspond to the foreign key column to ``thisAttrNames``. 
``thatSideColumns``
    column(s) that correspond to the foreign key column to ``thatAttrNames``. 
``thatObject``
    the destination object
``thatAttrNames``
    attribute(s) in destination object to join to

In addition, ``joinTable()`` takes positional and keyword arguments,
similar to ``getSome()``; it will accept raw SQL and bind values or
``SQLOperator`` instances as positional arguments, and understands the
keyword arguments ``order``, ``limit``, and ``offset`` as well as
column name keyword arguments.  Also, if you wish to pass in
additional tables to the select, you can do so with the
``extraTables`` keyword argument, with which you can pass a single
table name, or a list of names.

Getting Data From Multiple Tables At Once
+++++++++++++++++++++++++++++++++++++++++

PyDO includes a number of classes that join two ``PyDO`` classes and
make it possible to get pairs of instances of those classes at once in
a single query, closely modelling (and generating) SQL joins:
``CrossJoin``, ``InnerJoin``, ``RightJoin``, ``LeftJoin``,
``FullJoin``, ``NaturalInnerJoin``, ``NaturalRightJoin``,
``NaturalLeftJoin``, and ``NaturalFullJoin``.  ``CrossJoin`` and all
the natural joins have constructors of this form::

   Join(leftObject, rightObject...)

Whereas the rest take two additional parameters::

   Join(leftObject, rightObject, on=None, using=None)

The ``on`` and ``using`` parameters are mutually exclusive.  If
supplied, ``on`` may be a ``SQLOperator`` instance, a sequence of
``SQLOperator`` instances, a SQL string, or a sequence of which the
first element is a string and the rest are bind variables; ``using``,
if supplied instead, must be a sequence of field names.  

To issue a query, call the ``getSome()`` method on the join instance::

    >>> j1=CrossJoin(Teachers, Students)
    >>> res=j1.getSome(order=('teacher.lastname DESC', 
    ...                       'students.lastname DESC'), 
    ...                limit=1)
    >>> res[0][0].lastname, res[0][1].lastname
    Zyznowski, Yeoman
    
This ``getSome`` takes the same arguments as ``PyDO.getSome()``, but,
unlike it, is an instance method.

.. note:: All of these classes generate SQL using the SQL92 JOIN
    syntax, and not all the database systems supported by PyDO accept all
    these JOINS at all or in exactly the same way.

Currently these classes do not nest; the objects passed to the
constructor must be ``PyDO`` classes, not joins themselves.  Nested joins
may be supported in future.

If you want to join multiple tables and get ``PyDO`` instances back
without using JOIN syntax, that is possible using the ``arrayfetch``
method::

   arrayfetch(objs, *args)

Currently ``args`` must be a SQL string, followed by any bind variables.
 

.. note:: The various Join classes and ``arrayfetch`` are experimental
    features, subject to change.  

Managing Database Connections
-----------------------------

All that a ``PyDO`` class knows about its database connection is its
``connectionAlias`` attribute.  Before you use the class, you must
call ``initAlias()`` to associate that alias with the data needed to
make an actual database connection::

  initAlias(alias, driver, connectArgs, pool=False, verbose=False)

``driver`` must be the name of a driver registered with PyDO; the
built-in ones are currently "mysql", "psycopg", and "sqlite".
``connectArgs`` are arguments to pass to the underlying DBAPI driver's
``connect()`` function; you can pass a tuple of positional args, a
dictionary of keyword args, or a single object that will be treated
like a tuple of length 1. ``pool`` is an optional connection pool; if
you want one, you can either pass a ``ConnectionPool`` instance or
something with a compatible ``connect()`` method, or a true value, in
which case a default ``ConnectionPool`` will be created.  By default
no pool is used.  ``verbose`` is whether or not to log the generated
SQL; by default no logging is done.

The class method ``PyDO.getDBI()`` returns a database interface object
(an instance of a driver-specific ``PyDO.dbi.DBIBase`` subclass),
which in turn uses an underlying DBAPI database connection.  The DBAPI
connection is stored in thread-local storage and created lazily when
an attempt is made to access it, so transactions in different threads
will transparently use different connections.  By default the
connection will live as long as the current thread.  If you use a
pool, every time a transaction is completed, the connection will be
released by the DBI object and returned to the pool.  If you aren't
using a pool and are using multiple threads, when the thread is
finished, its connection will go out of scope and will get closed
during garbage collection.

If you want to manage connections outside of PyDO, you can, by using
the DBI object's ``swapConnection()`` method::

   oldConnection=myDBI.swapConnection(newConnection)
   # do something with PyDO
   
Because the connections are stored thread-locally, this is
thread-safe.  Using this technique, one could juggle multiple
transactions in the same process without using multiple threads.


Connection Pools
++++++++++++++++

If you are using transactions in multiple threads, a connection pool
can reduce the cost of connecting to the database.  The constructor
has this signature::

    pool=ConnectionPool(max_poolsize=0, 
                        keep_poolsize=1, 
                        delay=0.2,
                        retries=10)

``max_poolsize`` is the maximum number of connections it will permit
you to have in the pool at any one time; if 0, there is no upper
limit. ``keep_poolsize`` is the maximum number of connections it will
retain in the pool.  (In other words, the pool may grow up to
``max_poolsize``, but it will keep getting reduced to
``keep_poolsize`` when connections are released.)  ``delay`` is the
number of seconds it will delay if it needs to retry getting a
connection, because the pool has reached its maximum size; ``retries``
is the number of times to retry before giving up and raising a
``PyDOError``. 


A Complete Example
------------------

Consider the following toy sqlite database:

.. include:: examples/pim.sql
   :literal:

The following Python module wraps its tables in an api:

.. include:: examples/pim.py
   :literal: 



Differences From PyDO 1
-----------------------

This version of PyDO differs in several ways from PyDO version 1.x,
most notably: 

1.  PyDO1 defines fields as a tuple of tuples (fieldname, dbtype);
    type is  required, as PyDO1 drivers take much of the responsibility 
    for marshalling Python data types to database types, and does so as
    a function of column type.  PyDO2 does not need to know about what
    the database type is of the underlying columns, because DBAPI
    drivers now largely take care of this themselves.
2.  You cannot define uniqueness constraints in the field list in
    PyDO1.   
3.  Sequences and auto-increment fields are handled separately in
    PyDO1, and both have to be declared in separate class attributes,
    which have been dropped in PyDO2.
4.  The ``SQLOperator`` syntax is now more flexible, and is accepted by
    ``getSome()``. In PyDO1, there are three additional methods that
    accept different query syntaxes: ``getSomeWhere()``,
    ``getTupleWhere()``, and ``getSQLWhere()``. These have been 
    dropped.  ``joinTable()`` now accepts this query syntax as well, 
    so it is no longer necessary to override a protected method to 
    add additional criteria to a join query.
5.  PyDO1 is not thread-safe, and has no connection pool facilities
    for multi-threaded use.  What connection management facilities it
    does have are tied in with SkunkWeb.  PyDO2 is entirely separate
    from SkunkWeb.
6.  PyDO1 uses a different package structure; the new version does not
    have the same sub-modules.  However, everything you would normally
    need is available in the top-level namespace for both versions.
7.  PyDO1 does not have projections, and the inheritance semantics,
    while similar, are not exactly the same.
8.  PyDO1 does not use new-style classes (as it predates them), so the
    metaclass functionality is more elaborate, including its own
    implementation of class methods (which it calls "static"
    methods). 
9.  PyDO1 supports more databases than PyDO2 does at the time of
    writing.
10. PyDO2 does not implement PyDO1's ``scatterFetch()`` method, which
    returns multiple ``PyDO`` objects of different types in a single
    query. Related functionality is implemented by  ``arrayfetch()``
    and the Join classes, but they are subject to change during the
    alpha release cycle.
11. PyDO1 has a variable ``SYSDATE`` that means the current
    datetime, regardless of the underlying db.  PYDO2 does not
    abstract this, as it seems unnecessary now; you can use
    something database-dependent like
    ``CONSTANT('CURRENT_TIMESTAMP')`` or ``mx.DateTime.now()``. 





..
   Local Variables:
   mode: rst
   indent-tabs-mode: nil
   sentence-end-double-space: t
   fill-column: 70
   End:
