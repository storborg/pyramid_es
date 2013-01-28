from unittest import TestCase

from ..mixin import ElasticMixin, ESMapping, ESProp


def rgb_to_hex(rgb):
    return ('#' + ('%02x' * 3)) % rgb


class ESColor(ESProp):
    def __init__(self, name, *args, **kwargs):
        ESProp.__init__(self, name, *args, filter=rgb_to_hex, **kwargs)


class Thing(object):
    def __init__(self, id, foreground, child=None):
        self.id = id
        self.foreground = foreground
        self.child = child


class TestMixin(TestCase):

    def test_custom_prop(self):
        mapping = ESColor('foreground')

        obj = Thing(id=42, foreground=(60, 40, 30))
        doc = mapping(obj)

        self.assertEqual(doc, '#3c281e')

    def test_elastic_mixin_no_mapping(self):
        class Foo(ElasticMixin):
            pass

        with self.assertRaises(NotImplementedError):
            Foo.elastic_mapping()

    def test_nested_mappings(self):
        mapping = ESMapping(
            analyzer='lowercase',
            properties=ESMapping(
                ESColor('foreground'),
                child=ESMapping(
                    analyzer='lowercase',
                    properties=ESMapping(
                        ESColor('foreground')))))

        thing1 = Thing(id=1,
                       foreground=(40, 20, 27))
        thing2 = Thing(id=2,
                       foreground=(37, 88, 19),
                       child=thing1)

        doc = mapping(thing2)
        self.assertEqual(doc['_id'], 2)
        self.assertEqual(doc['child']['_id'], 1)

    def test_nested_mappings_dict(self):
        mapping = ESMapping(
            analyzer='lowercase',
            properties=ESMapping(
                ESColor('foreground'),
                child=dict(
                    analyzer='lowercase',
                    properties=ESMapping(
                        ESColor('foreground')))))

        thing1 = Thing(id=1,
                       foreground=(40, 20, 27))
        thing2 = Thing(id=2,
                       foreground=(37, 88, 19),
                       child=thing1)

        doc = mapping(thing2)
        self.assertEqual(doc['_id'], 2)
        self.assertEqual(doc['child']['_id'], 1)
