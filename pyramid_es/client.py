import logging

from itertools import chain
from pprint import pformat

import six

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from .query import ElasticQuery
from .result import ElasticResultRecord

log = logging.getLogger(__name__)


ANALYZER_SETTINGS = {
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


CREATE_INDEX_SETTINGS = ANALYZER_SETTINGS.copy()
CREATE_INDEX_SETTINGS.update({
    "index": {
        "number_of_shards": 2,
        "number_of_replicas": 0
    },
})


class ElasticClient(object):
    """
    A handle for interacting with the Elasticsearch backend.
    """

    def __init__(self, servers, index, timeout=1.0, disable_indexing=False):
        self.index = index
        self.disable_indexing = disable_indexing
        self.es = Elasticsearch(servers)

    def ensure_index(self, recreate=False):
        """
        Ensure that the index exists on the ES server, and has up-to-date
        settings.
        """
        exists = self.es.indices.exists(self.index)
        if recreate or not exists:
            if exists:
                self.es.indices.delete(self.index)
            self.es.indices.create(self.index,
                                   body=dict(settings=CREATE_INDEX_SETTINGS))

    def delete_index(self):
        """
        Delete the index on the ES server.
        """
        self.es.indices.delete(self.index)

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

        doc_mapping = {doc_type: doc_mapping}

        log.debug('Putting mapping: \n%s', pformat(doc_mapping))
        if recreate:
            try:
                self.es.indices.delete_mapping(index=self.index,
                                               doc_type=doc_type)
            except NotFoundError:
                pass
        self.es.indices.put_mapping(index=self.index,
                                    doc_type=doc_type,
                                    body=doc_mapping)

    def delete_mapping(self, cls):
        """
        Delete the mapping corresponding to ``cls`` on the server. Does not
        delete subclass mappings.
        """
        doc_type = cls.__name__
        self.es.indices.delete_mapping(index=self.index,
                                       doc_type=doc_type)

    def ensure_all_mappings(self, base_class, recreate=False):
        """
        Initialize explicit mappings for all subclasses of the specified
        SQLAlcehmy declarative base class.
        """
        for cls in base_class._decl_class_registry.values():
            if hasattr(cls, 'elastic_mapping'):
                self.ensure_mapping(cls, recreate=recreate)

    def get_mappings(self, cls=None):
        """
        Return the object mappings currently used by ES.
        """
        doc_type = cls and cls.__name__
        return self.es.indices.get_mapping(index=self.index,
                                           doc_type=doc_type)

    def index_object(self, obj):
        """
        Add or update the indexed document for an object.
        """
        doc = obj.elastic_document()

        doc_type = obj.__class__.__name__
        doc_id = doc.pop("_id")
        doc_parent = obj.elastic_parent

        log.debug('Indexing object:\n%s', pformat(doc))
        log.debug('Type is %r', doc_type)
        log.debug('ID is %r', doc_id)
        log.debug('Parent is %r', doc_parent)

        self.index_document(id=doc_id,
                            doc_type=doc_type,
                            doc=doc,
                            parent=doc_parent)

    def index_document(self, id, doc_type, doc, parent=None):
        """
        Add or update the indexed document from a raw document source (not an
        object).
        """
        if self.disable_indexing:
            return

        kwargs = dict(index=self.index,
                      body=doc,
                      doc_type=doc_type,
                      id=id)
        if parent:
            kwargs['parent'] = parent
        self.es.index(**kwargs)

    def index_objects(self, objects):
        """
        Add multiple objects to the index.
        """
        for obj in objects:
            self.index_object(obj)

        self.es.indices.flush(force=True)

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

        kwargs = dict(index=self.index,
                      doc_type=doc_type,
                      id=doc_id)
        if routing:
            kwargs['routing'] = routing
        r = self.es.get(**kwargs)
        return ElasticResultRecord(r)

    def refresh(self):
        """
        Refresh the ES index.
        """
        self.es.indices.refresh(index=self.index)

    def subtype_names(self, cls):
        """
        Return a list of document types to query given an object class.
        """
        classes = [cls] + [m.class_ for m in
                           cls.__mapper__._inheriting_mappers]
        return [c.__name__ for c in classes
                if hasattr(c, "elastic_mapping")]

    def search(self, body, classes=None, fields=None, **query_params):
        """
        Run ES search using default indexes.
        """
        doc_types = classes and list(chain.from_iterable(
            [doc_type] if isinstance(doc_type, six.string_types) else
            self.subtype_names(doc_type)
            for doc_type in classes))

        if fields:
            query_params['fields'] = fields

        return self.es.search(index=self.index,
                              doc_type=','.join(doc_types),
                              body=body,
                              **query_params)

    def query(self, *classes, **kw):
        """
        Return an ElasticQuery against the specified class.
        """
        cls = kw.pop('cls', ElasticQuery)
        return cls(client=self, classes=classes, **kw)

    def analyze(self, text, analyzer):
        """
        Preview the result of analyzing a block of text using a given analyzer.
        """
        return self.es.indices.analyze(index=self.index,
                                       analyzer=analyzer,
                                       text=text)
