import logging

from itertools import chain
from pprint import pformat

import pyes

from .query import ElasticQuery

log = logging.getLogger(__name__)


"The standard Elastic Search index definition."
UPDATE_INDEX_DEFAULTS = {
    "analysis": {
        "filter": {
            "snowball": {
                "type": "snowball",
                "language": "English"
            },
        },

        "analyzer": {
            "lowercase": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["standard", "lowercase"]
            },

            "email": {
                "type": "custom",
                "tokenizer": "uax_url_email",
                "filter": ["standard", "lowercase"]
            },

            "content": {
                "type": "custom",
                "tokenizer": "standard",
                "char_filter": ["html_strip"],
                "filter": ["standard", "lowercase", "stop", "snowball"]
            }
        }
    }
}


CREATE_INDEX_DEFAULTS = UPDATE_INDEX_DEFAULTS.copy()
CREATE_INDEX_DEFAULTS.update({
    "index": {
        "number_of_shards": 2,
        "number_of_replicas": 0
    },
})


class CustomTimeout(object):
    def __init__(self, es, timeout, retry_time):
        self.cnx = es.connection
        self.timeout = timeout
        self.retry_time = retry_time

    def __enter__(self):
        cnx = self.cnx
        self.orig_rt, cnx._retry_time = cnx._retry_time, self.retry_time
        self.orig_to, cnx._timeout = cnx._timeout, self.timeout

    def __exit__(self, type, value, traceback):
        cnx = self.cnx
        cnx._retry_time = self.orig_rt
        cnx._timeout = self.orig_to


class ElasticClient(object):

    def __init__(self, servers, index, timeout=1.0, disable_indexing=False):
        self.index = index
        self.disable_indexing = disable_indexing
        self.es = pyes.ES(servers, timeout=timeout)

    def custom_timeout(self, timeout, retry_time=60):
        return CustomTimeout(es=self.es,
                             timeout=timeout,
                             retry_time=retry_time)

    def ensure_index(self, recreate=False):
        """
        Ensure that the index exists on the ES server, and has up-to-date
        settings.
        """
        if recreate:
            try:
                self.es.delete_index(self.index)
            except pyes.exceptions.IndexMissingException:
                pass
        try:
            self.es.create_index(self.index, CREATE_INDEX_DEFAULTS)
        except pyes.exceptions.IndexAlreadyExistsException:
            self.es.update_settings(self.index, UPDATE_INDEX_DEFAULTS)

    def ensure_mapping(self, cls, recreate=False):
        """
        Put an explicit mapping for the given class if it doesn't already
        exist.
        """
        doc_type = cls.__name__
        doc_mapping = cls.elastic_mapping()

        doc_mapping = dict(doc_mapping)
        if cls.elastic_parent:
            doc_mapping["_parent"] = {
                "type": cls.elastic_parent
            }

        if recreate:
            try:
                self.es.delete_mapping(self.index, doc_type)
            except pyes.exceptions.TypeMissingException:
                pass
        log.debug('Putting mapping: \n%s', pformat(doc_mapping))
        self.es.put_mapping(doc_type, doc_mapping, [self.index])

    def ensure_all_mappings(self, base_class, recreate=False):
        """
        Initialize explicit mappings for all subclasses of the specified
        SQLAlcehmy declarative base class.
        """
        for cls in base_class._decl_class_registry.itervalues():
            if hasattr(cls, 'elastic_mapping'):
                self.ensure_mapping(cls, recreate=recreate)

    def index_object(self, obj, bulk=False):
        """
        Add or update the indexed document for an object.
        """
        if self.disable_indexing:
            return

        doc = obj.elastic_document()

        doc_type = obj.__class__.__name__
        doc_id = doc.pop("_id")
        doc_parent = obj.elastic_parent

        log.debug('Indexing object:\n%s', pformat(doc))
        log.debug('Type is %r', doc_type)
        log.debug('ID is %r', doc_id)
        log.debug('Parent is %r', doc_parent)
        self.es.index(doc, self.index, doc_type, id=doc_id,
                      parent=doc_parent, bulk=bulk)

    def index_objects(self, objects):
        """
        Add multiple objects to the index.
        """
        for obj in objects:
            self.index_object(obj, bulk=True)

        with self.custom_timeout(None):
            self.es.flush_bulk(forced=True)

    def get(self, obj, routing=None):
        """
        Retrieve the ES source document for a given object or (document type,
        id) pair.
        """
        if isinstance(obj, tuple):
            doc_type, doc_id = obj
        else:
            doc_type, doc_id = obj.__class__.__name__, obj.id
            if obj.elastic_parent:
                routing = obj.elastic_parent

        return self.es.get(self.index, doc_type, doc_id, routing=routing)

    def subtype_names(self, cls):
        """
        Return a list of document types to query given an object class.
        """
        classes = [cls] + [m.class_ for m in
                           cls.__mapper__._inheriting_mappers]
        return [c.__name__ for c in classes
                if hasattr(c, "elastic_mapping")]

    def search(self, query, classes=None, **query_params):
        """
        Run ES search using default indexes.
        """
        doc_types = classes and list(chain.from_iterable(
            [doc_type] if isinstance(doc_type, basestring) else
            self.subtype_names(doc_type)
            for doc_type in classes))

        log.debug('Running query:\n%s', pformat(query.serialize()))
        res = self.es.search(query, indices=[self.index],
                             doc_types=doc_types, **query_params)
        res.hits
        log.debug('Query complete.')
        return res

    def get_mappings(self, cls=None):
        """
        Return the object mappings currently used by ES.
        """
        doc_type = cls and cls.__name__
        return self.es.get_mapping(doc_type=doc_type, indices=[self.index])

    def query(self, *classes, **kw):
        """
        Return an ElasticQuery against the specified class.
        """
        return ElasticQuery(client=self, classes=classes, **kw)

    def refresh(self):
        self.es.refresh(indices=[self.index])
