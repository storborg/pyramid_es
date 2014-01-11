"""
Utility classes intended to make it easier to specify Elastic Search mappings
for model objects.
"""


class ElasticParent(object):
    """
    Descriptor to return the parent document type of a class or the parent
    document ID of an instance.

    The child class should specify a property:

    __elastic_parent__ = ('ParentDocType', 'parent_id_attr')
    """

    def __get__(self, instance, owner):
        if owner.__elastic_parent__ is None:
            return None
        if instance is None:
            return owner.__elastic_parent__[0]
        return getattr(instance, owner.__elastic_parent__[1])


class ElasticMixin(object):
    """
    Mixin for SQLAlchemy classes that use ESMapping.
    """

    __elastic_parent__ = None

    @classmethod
    def elastic_mapping(cls):
        """
        Return an ES mapping for the current class. Should basically be some
        form of ``return ESMapping(...)``.
        """
        raise NotImplementedError("ES classes must define a mapping")

    def elastic_document(self):
        "Apply the class ES mapping to the current instance."
        return self.elastic_mapping()(self)

    elastic_parent = ElasticParent()


class ESMapping(object):
    """
    ESMapping defines a tree-like DSL for building Elastic Search mappings.

    Calling dict(es_mapping_object) produces an Elastic Search mapping
    definition appropriate for pyes.

    Applying an ESMapping to another object returns an Elastic Search document.
    """

    def __init__(self, *args, **kwargs):
        self.filter = kwargs.pop("filter", None)
        self.name = kwargs.pop("name", None)
        self.attr = kwargs.pop("attr", None)

        # Automatically map the id field
        self.parts = {"_id": ESField("_id", attr="id")}

        # Map implicit args
        for arg in args:
            self.parts[arg.name] = arg

        # Map explicit kwargs
        for k, v in kwargs.items():
            if isinstance(v, dict):
                v, v.parts = ESMapping(), v
            if isinstance(v, ESMapping):
                v.name = k
            self.parts[k] = v

    def __iter__(self):
        for k, v in self.parts.items():
            if isinstance(v, ESMapping):
                v = dict(v)
            if v:
                yield k, v

    iteritems = __iter__
    items = __iter__

    @property
    def properties(self):
        """
        Return the dictionary {name: property, ...} describing the top-level
        properties in this mapping, or None if this mapping is a leaf.
        """
        props = self.parts.get("properties")
        if props:
            return props.parts

    def __call__(self, instance):
        """
        Apply this mapping to an instance to return a document.

        Returns a dictionary {name: value, ...}.
        """
        if self.attr or self.name:
            instance = getattr(instance, self.attr or self.name)
        if self.filter:
            instance = self.filter(instance)
        if self.properties is None:
            return instance
        return dict((k, v(instance)) for k, v in self.properties.items())


class ESProp(ESMapping):
    "A leaf property."
    def __init__(self, name, filter=None, attr=None, **kwargs):
        self.name = name
        self.attr = attr
        self.filter = filter
        self.parts = kwargs


class ESField(ESProp):
    """
    A leaf property that doesn't emit a mapping definition.

    This behavior is useful if you want to allow Elastic Search to
    automatically construct an appropriate mapping while indexing.
    """
    def __iter__(self):
        return iter(())


class ESString(ESProp):
    "A string property."
    def __init__(self, name, **kwargs):
        ESProp.__init__(self, name, type="string", **kwargs)
