import logging

import copy
from functools import wraps
from collections import OrderedDict

import six

from .result import ElasticResult

log = logging.getLogger(__name__)

ARBITRARILY_LARGE_SIZE = 100000


def generative(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        self = self._generate()
        f(self, *args, **kwargs)
        return self
    return wrapped


def filters(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        val = f(self, *args, **kwargs)
        self.filters.append(val)
    return wrapped


class ElasticQuery(object):

    def __init__(self, client, classes=None, q=None):
        if not q:
            q = self.match_all_query()
        elif isinstance(q, six.string_types):
            q = self.text_query(q, operator='and')

        self.base_query = q
        self.client = client
        self.classes = classes

        self.filters = []
        self.sorts = OrderedDict()
        self.facets = {}

        self._size = None
        self._start = None

    def _generate(self):
        s = self.__class__.__new__(self.__class__)
        s.__dict__ = self.__dict__.copy()
        s.filters = list(s.filters)
        s.sorts = s.sorts.copy()
        s.facets = s.facets.copy()
        return s

    @staticmethod
    def match_all_query():
        return {
            'match_all': {}
        }

    @staticmethod
    def text_query(phrase, operator="and"):
        return {
            "text": {
                '_all': {
                    "query": phrase,
                    "operator": operator,
                    "analyzer": "content"
                }
            }
        }

    @generative
    @filters
    def filter_term(self, term, value):
        return {'term': {term: value}}

    @generative
    @filters
    def filter_terms(self, term, value):
        return {'terms': {term: value}}

    @generative
    @filters
    def filter_value_upper(self, term, upper):
        return {'range': {term: {'to': upper, 'include_upper': True}}}

    @generative
    @filters
    def filter_value_lower(self, term, lower):
        return {'range': {term: {'from': lower, 'include_lower': True}}}

    @generative
    def order_by(self, key, desc=False):
        order = "desc" if desc else "asc"
        self.sorts['order_by_%s' % key] = {key: {"order": order}}

    @generative
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

    @generative
    def offset(self, n):
        if self._start is not None:
            raise ValueError('This query already has an offset applied.')
        self._start = n
    start = offset

    @generative
    def limit(self, n):
        if self._size is not None:
            raise ValueError('This query already has a limit applied.')
        self._size = n
    size = limit

    def _search(self, start=None, size=None, fields=None):
        q = copy.copy(self.base_query)

        if self.filters:
            f = {'and': self.filters}
            q = {
                'filtered': {
                    'filter': f,
                    'query': q,
                }
            }

        q_start = self._start or 0
        q_size = self._size or ARBITRARILY_LARGE_SIZE

        if size is not None:
            q_size = max(0,
                         size if q_size is None else
                         min(size, q_size - q_start))

        if start is not None:
            q_start = q_start + start

        body = {
            'sort': list(self.sorts.values()),
            'query': q
        }
        if self.facets:
            body['facets'] = self.facets

        return self.client.search(body, classes=self.classes, fields=fields,
                                  size=q_size, from_=q_start)

    def execute(self, start=None, size=None, fields=None):
        return ElasticResult(self._search(start=start, size=size,
                                          fields=fields))

    def count(self):
        res = self._search(size=0)
        return res['hits']['total']
