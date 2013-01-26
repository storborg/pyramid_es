"""
Utilities for constructing and executing ES queries.
"""
import copy
from functools import wraps
from itertools import chain
from collections import OrderedDict

import pyes


class QueryWrapper(pyes.Query):
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


def first_or_none(things):
    """
    Return the first element of an iterable or None if it's empty.
    """
    return next(iter(things), None)


def except_null(elts):
    """
    Return the non-None elements of elts.

    :rtype:
      List if elts is a list. Otherwise a generator.
    """
    if isinstance(elts, list):
        return [x for x in elts if x is not None]
    return (x for x in elts if x is not None)


def except_null_reducer(reducer):
    def f(*args):
        args = list(except_null(args))
        return reducer(args) if len(args) > 1 else first_or_none(args)
    return f


and_filter = except_null_reducer(pyes.ANDFilter)
or_filter = except_null_reducer(pyes.ORFilter)


def _setter(prop):
    def dec(f):
        name = f.__name__

        @wraps(f)
        def func(self, *args, **kwargs):
            p = getattr(self, prop)
            v = f(self, *args, **kwargs)
            if v is None:
                p.pop(name, None)
            elif isinstance(v, list):
                p.setdefault(name, []).extend(v)
            elif isinstance(v, tuple):
                p["%s_%s" % (name, v[0])] = v[1]
            else:
                p[name] = v
        return func
    return dec

_filter = _setter("filters")
_sort = _setter("sorts")


class ElasticQuery(object):
    def __init__(self, client, q=None, doc_types=None):
        if q is None:
            q = pyes.MatchAllQuery()
        self.base_query = q

        self.doc_types = doc_types
        self.fields = []
        self.filters = OrderedDict()
        self.sorts = OrderedDict()
        self._limit = None
        self.client = client

    def query_text(self, phrase, operator='and'):
        "General text query for products."
        self.base_query = text_query('_all', phrase, operator=operator)

    def _es_filter(self):
        return and_filter(*chain.from_iterable(
            ([v] if isinstance(v, (dict, type(None), pyes.Filter)) else v)
            for v in self.filters.itervalues()))

    def _es_query(self):
        f = self._es_filter()

        q = copy.copy(self.base_query)
        if f is not None:
            q = pyes.FilteredQuery(q, f)

        q = q.search()
        q.sort = self.sorts.values()
        q.fields = self.fields
        q.start = 0
        q.size = self._limit
        return q

    def _search(self, start=None, size=None, facet=None, fields=None,
                **search_args):
        q = self._es_query()
        q_start, q_size = q.start, q.size

        if start is not None:
            q.start = q_start + start
        if size is not None:
            q.size = max(0, size if q_size is None else
                         min(size, q_size - q.start))
        if facet is not None:
            q.facet = facet
        if fields is not None:
            q.fields = fields

        return self.client.search(q, doc_types=self.doc_types, **search_args)

    def __iter__(self):
        pass

    def all(self):
        res = self._search()
        return res.hits

    def count(self):
        res = self._search(size=0)
        return res.total

    def limit(self, v):
        self._limit = v

    @_filter
    def filter_term(self, term, value):
        return (term, pyes.TermFilter(term, value))

    @_sort
    def order_by(self, key, descending=False):
        order = "desc" if descending else "asc"
        return (key, {key: {"order": order}})
