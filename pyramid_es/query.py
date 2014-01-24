import logging

import copy
from functools import wraps
from collections import OrderedDict

import six

from .result import ElasticResult

log = logging.getLogger(__name__)

ARBITRARILY_LARGE_SIZE = 100000


def generative(f):
    """
    A decorator to wrap query methods to make them automatically generative.
    """
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        self = self._generate()
        f(self, *args, **kwargs)
        return self
    return wrapped


def filters(f):
    """
    A convenience decorator to wrap query methods that are adding filters. To
    use, simply make a method that returns a filter dict in elasticsearch's
    JSON object format.

    Should be used inside @generative (listed after in decorator order).
    """
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        val = f(self, *args, **kwargs)
        self.filters.append(val)
    return wrapped


class ElasticQuery(object):
    """
    Represents a query to be issued against the ES backend.
    """

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
        """
        Static method to return a filter dict which will match everything. Can
        be overridden in a subclass to customize behavior.
        """
        return {
            'match_all': {}
        }

    @staticmethod
    def text_query(phrase, operator="and"):
        """
        Static method to return a filter dict to match a text search. Can be
        overridden in a subclass to customize behavior.
        """
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
        """
        Filter for documents where the field ``term`` matches ``value``.
        """
        return {'term': {term: value}}

    @generative
    @filters
    def filter_terms(self, term, value):
        """
        Filter for documents where the field ``term`` matches one of the
        elements in ``value`` (which should be a sequence).
        """
        return {'terms': {term: value}}

    @generative
    @filters
    def filter_value_upper(self, term, upper):
        """
        Filter for documents where term is numerically less than ``upper``.
        """
        return {'range': {term: {'to': upper, 'include_upper': True}}}

    @generative
    @filters
    def filter_value_lower(self, term, lower):
        """
        Filter for documents where term is numerically more than ``lower``.
        """
        return {'range': {term: {'from': lower, 'include_lower': True}}}

    @generative
    def order_by(self, key, desc=False):
        """
        Sort results by the field ``key``. Default to ascending order, unless
        ``desc`` is True.
        """
        order = "desc" if desc else "asc"
        self.sorts['order_by_%s' % key] = {key: {"order": order}}

    @generative
    def add_facet(self, facet):
        """
        Add a query facet, to return data used for the implementation of
        faceted search (e.g. returning result counts for given possible
        sub-queries).

        The facet should be supplied as a dict in the format that ES uses for
        representation.

        It is recommended to use the helper methods ``add_term_facet()`` or
        ``add_range_facet()`` where possible.
        """
        self.facets.update(facet)

    def add_term_facet(self, name, size, field):
        """
        Add a term facet.

        ES will return data about document counts for the top sub-queries (by
        document count) in which the results are filtered by a given term.
        """
        return self.add_facet({
            name: {
                'terms': {
                    'field': field,
                    'size': size
                }
            }
        })

    def add_range_facet(self, name, field, ranges):
        """
        Add a range facet.

        ES will return data about documetn counts for the top sub-queries (by
        document count) inw hich the results are filtered by a given numerical
        range.
        """
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
        """
        When returning results, start at document ``n``.
        """
        if self._start is not None:
            raise ValueError('This query already has an offset applied.')
        self._start = n
    start = offset

    @generative
    def limit(self, n):
        """
        When returning results, stop at document ``n``.
        """
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
        """
        Execute this query and return a result set.
        """
        return ElasticResult(self._search(start=start, size=size,
                                          fields=fields))

    def count(self):
        """
        Execute this query to determine the number of documents that would be
        returned, but do not actually fetch documents. Returns an int.
        """
        res = self._search(size=0)
        return res['hits']['total']
