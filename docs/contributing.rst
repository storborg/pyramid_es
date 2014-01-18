Contributing
============

Patches and suggestions are strongly encouraged! Github pull requests are
preferred, but other mechanisms of feedback are welcome.

pyramid_es has a comprehensive test suite with 100% line and branch coverage,
as reported by the excellent ``coverage`` module. To run the tests, simply run
in the top level of the repo::

    $ nosetests

There are no `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ or
`Pyflakes <http://pypi.python.org/pypi/pyflakes>`_ warnings in the codebase. To
verify that::

    $ pip install pep8 pyflakes
    $ pep8 .
    $ pyflakes .

Any pull requests must maintain the sanctity of these three pillars.

You can test these three things on all supported platforms with Tox::

    $ tox
