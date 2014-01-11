import logging

import copy
from functools import wraps
from collections import OrderedDict

import six

from .result import ElasticResult

log = logging.getLogger(__name__)


class QueryWrapper(object):
    "Wrap a dictionary for consumption by pyes."
    def __init__(self, q):
        assert isinstance(q, dict)
        self.q = q

    def serialize(self):
        return self.q


def text_query(field, phrase, operator="and"):
    return QueryWrapper({"text": {
        field: {
            "query": phrase,
            "operator": operator,
            "analyzer": "content"}}})


def match_all_query():
    return QueryWrapper({
        'match_all': {}
    })


def _generative(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        self = self._generate()
        f(self, *args, **kwargs)
        return self
    return wrapped


def _setter(prop):
    def dec(f):
        name = f.__name__

        @wraps(f)
        def func(self, *args, **kwargs):
            p = getattr(self, prop)
            v = f(self, *args, **kwargs)
            if isinstance(v, tuple):
                p["%s_%s" % (name, v[0])] = v[1]
            else:
                p[name] = v
        return func
    return dec

_filter = _setter("filters")
_sort = _setter("sorts")


class ElasticQuery(object):

    def __init__(self, client, classes=None, q=None):
        if not q:
            #q = pyes.MatchAllQuery()
            q = match_all_query()
        elif isinstance(q, six.string_types):
            q = text_query('_all', q, operator='and')
        else:
            q = QueryWrapper(q)

        self.base_query = q
        self.client = client
        self.classes = classes

        self.filters = OrderedDict()
        self.sorts = OrderedDict()
        self.facets = {}

        self._size = None
        self._start = None

    def _generate(self):
        s = self.__class__.__new__(self.__class__)
        s.__dict__ = self.__dict__.copy()
        s.filters = s.filters.copy()
        s.sorts = s.sorts.copy()
        s.facets = s.facets.copy()
        return s

    @_generative
    @_filter
    def filter_term(self, term, value):
        return {'term': {term: value}}

    @_generative
    @_filter
    def filter_value_upper(self, term, upper):
        return {'range': {term: {'to': upper, 'include_upper': True}}}

    @_generative
    @_filter
    def filter_value_lower(self, term, lower):
        return {'range': {term: {'from': lower, 'include_lower': True}}}

    @_generative
    @_sort
    def order_by(self, key, desc=False):
        order = "desc" if desc else "asc"
        return (key, {key: {"order": order}})

    @_generative
    def limit(self, v):
        if self._size:
            raise ValueError('This query already has a limit applied.')
        self._size = v

    @_generative
    def offset(self, v):
        if self._start:
            raise ValueError('This query already has an offset applied.')
        self._start = v

    @_generative
    def add_facet(self, facet):
        self.facets.update(facet)

    def add_term_facet(self, name, size, field):
        return self.add_facet({
            name: {
                'terms': {
                    'field': field,
                    'size': size
                }
            }
        })

    def add_range_facet(self, name, field, ranges):
        return self.add_facet({
            name: {
                'range': {
                    'field': field,
                    'ranges': ranges,
                }
            }
        })

    def compile(self):
        q = copy.copy(self.base_query)

        if self.filters:
            f = {'and': list(self.filters.values())}
            q = QueryWrapper({
                'filtered': {
                    'filter': f,
                    'query': q.serialize(),
                }
            })

        q.sort = list(self.sorts.values())
        q.size = self._size
        q.start = self._start or 0
        q.facets = self.facets

        return q

    def _search(self, size=None):
        q = self.compile()

        if size is not None:
            q_size = q.size
            q.size = max(0, size if q_size is None else
                         min(size, q_size - q.start))

        return self.client.search(q, classes=self.classes)

    def execute(self):
        return ElasticResult(self._search())

    def count(self):
        res = self._search(size=0)
        return res['hits']['total']
