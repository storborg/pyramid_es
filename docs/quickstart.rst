Quick Start
===========


Install
-------

Install with pip::

    $ pip install pyramid_es


Integrate with a Pyramid App
----------------------------

Include pyramid_es, by calling ``config.include('pyramid_es')`` or adding
pyramid_es to ``pyramid.includes``.

Configure the following settings:

* ``elastic.servers``
* ``elastic.timeout``
* ``elastic.index``

* ``elastic.disable_indexing``


Add the Mixin Class to a Model
------------------------------

Add ``ElasticMixin`` to a model class. For example:

.. code-block:: python

    from pyramid_es.mixin import ElasticMixin

    class Article(Base, ElasticMixin):
        ...

Then implement the ``elastic_mapping()`` class method:

.. code-block:: python

    from pyramid_es.mixin import ElasticMixin, ESMapping, ESString, ESField

    class Article(Base, ElasticMixin):
        ...

        @classmethod
        def elastic_mapping(cls):
            return ESMapping(
                return ESMapping(
                    analyzer='content',
                    properties=ESMapping(
                        ESString('title', boost=5.0),
                        ESString('body'),
                        ESField('pubdate'))))

You can customize the exact behavior of the mapping and document creation by
adjusting the ``elastic_mapping(cls)`` class method and the
``elastic_document(self)`` instance method.


Access the Client
-----------------

To interact with the elasticsearch server, use the client instance maintained by ``pyramid_es``. You can access it like:

.. code-block:: python

    from pyramid_es import get_client

    client = get_client(registry)

All operations--index maintenance, diagnostics, indexing, and querying--are performed via methods on this instance.


Index a Document
----------------

After the model class is prepared, index a document with:

.. code-block:: python

    client.index_object(article)

This call will create or update the elasticsearch backend state for this model
object, so you can simply call it any time the object is created or updated. If
the object is deleted, call:

.. code-block:: python

    client.delete_object(article)


Execute a Search Query
----------------------

Search queries are formed generatively, much like SQLAlchemy. Here's an example:

.. code-block:: python

    q = client.query(Article)
    q = q.filter_term('title', 'Introduction')
    q = q.order_by('pubdate', desc=True)
    results = q.execute()

    for result in results:
        print result.title, result.pubdate

To make a keyword search, add the ``q`` argument to ``client.query()``:

.. code-block:: python

    q = client.query(Article, q='kittens')

Calling a query method like ``.filter_term()`` or ``.order_by()`` will create a totally new query instance, and not modify the original.

You can use query methods to:

* Add filters on specific fields, range filters, or anything else supported by
  elasticsearch
* Sort by fields
* Add search facets


The Result Object
-----------------

Calling ``.execute()`` on a query issues the query to the backend and returns a
special result object. This object behaves similar to a dict, but supports
iteration and a few special properties.
