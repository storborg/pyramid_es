pyramid_es - Elasticsearch Integration for Pyramid
==================================================

Scott Torborg - `Cart Logic <http://www.cartlogic.com>`_

``pyramid_es`` is a pattern and set of utilities for integrating the
`elasticsearch <http://www.elasticsearch.org>`_ search engine with a `Pyramid
<http://www.pylonsproject.org>`_ web app. It is intended to make it easy to
index a set of persisted objects and search those documents inside Pyramid
views.


Installation
============

Install with pip::

    $ pip install pyramid_es


Overview
========

Your app is expected to use ``pyramid_es`` through three different points: a mapping mixin, a query builder, and a client interface.

The ``ElasticMixin`` mixin class provides some minimal functionality to allow
model classes to generate a document suitable for indexing.

The ``ElasticQuery`` class provides a mechanism to generate elasticsearch
search queries, much like, for example, the SQLAlchemy ``Query`` class.

The ``ElasticClient`` class provides an access point to configure elasticsearch, index objects, and make search queries. It is initialized automatically by ``pyramid_es`` and made available to your app as ``registry.es_client``.

A few settings are used to configure the ``ElasticClient`` instance for your app, with the following defaults::

    elastic.servers = localhost
    elastic.index = pyramid
    elastic.timeout = 1.0

Stay tuned for more...
