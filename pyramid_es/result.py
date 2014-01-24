from .dotdict import DotDict


class ElasticResultRecord(object):
    """
    Wrapper for an Elasticsearch result record. Provides access to the indexed
    document, ES result data (like score), and the mapped object.
    """
    def __init__(self, raw):
        self.raw = DotDict(raw)

    def __repr__(self):
        return '<%s score:%s id:%s type:%s>' % (
            self.__class__.__name__,
            getattr(self, '_score', '-'), self._id, self._type)

    def __getitem__(self, key):
        return self.raw[key]

    def __contains__(self, key):
        return key in self.raw

    def __getattr__(self, key):
        source = self.raw.get(u'_source', {})
        fields = self.raw.get(u'fields', {})
        if key in source:
            return source[key]
        elif key in fields:
            return fields[key]
        elif key in self.raw:
            return self.raw[key]
        raise AttributeError('%r object has no attribute %r' %
                             (self.__class__.__name__, key))


class ElasticResult(object):
    """
    Wrapper for an Elasticsearch result set. Provides access to the documents,
    result aggregate data (like total count), and facets.
    """
    def __init__(self, raw):
        self.raw = raw

    def __iter__(self):
        return (ElasticResultRecord(record)
                for record in self.raw['hits']['hits'])

    @property
    def total(self):
        """
        Return the total number of docs which would have been matched by this
        query. Note that this is not necessarily the same as the number of
        document result records associated with this object, because the query
        may have a start / size applied.
        """
        return self.raw['hits']['total']

    @property
    def facets(self):
        """
        Return the facets returned by this seach query.
        """
        return self.raw['facets']
