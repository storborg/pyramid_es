class ElasticResultRecord(object):
    """
    Wrapper for an Elasticsearch result record. Provides access to the indexed
    document, ES result data (like score), and the mapped object.
    """
    def __init__(self, raw):
        self.raw = raw

    def __repr__(self):
        return '<%s score:%s id:%s type:%s>' % (
            self.__class__.__name__,
            self._score, self._id, self._type)

    def __getattr__(self, key):
        source = self.raw[u'_source']
        if key in source:
            return source[key]
        elif key in self.raw:
            return self.raw[key]
        raise AttributeError('%r object has no attribute %r' %
                             (self.__class__.__name__, key))


class ElasticResult(object):

    def __init__(self, raw):
        self.raw = raw

    def __iter__(self):
        return (ElasticResultRecord(record)
                for record in self.raw['hits']['hits'])

    @property
    def count(self):
        return self.raw['hits']['total']

    @property
    def facets(self):
        return self.raw['facets']
