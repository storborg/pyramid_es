from unittest import TestCase

from ..mixin import ElasticMixin, ESMapping, ESString, ESProp


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

    def test_contains(self):
        mapping = ESMapping(
            ESString("name"),
            ESString("body"))
        self.assertIn('name', mapping)
        self.assertNotIn('foo', mapping)

    def test_getitem(self):
        name_field = ESString('name', analyzer='lowercase')
        mapping = ESMapping(
            name_field,
            ESString("body"))
        self.assertEqual(mapping['name'], name_field)
        self.assertEqual(mapping['name']['analyzer'], 'lowercase')

    def test_setitem(self):
        name_field = ESString('foo')
        name_field['analyzer'] = 'lowercase'
        self.assertEqual(name_field['analyzer'], 'lowercase')

    def test_update(self):
        mapping_base = ESMapping(
            ESString('name'),
            ESString('body'),
            ESString('color'))
        mapping_new = ESMapping(
            ESString('name', analyzer='lowercase'),
            ESString('foo'))
        self.assertNotIn('analyzer', mapping_base['name'])

        mapping_base.update(mapping_new)
        self.assertEqual(mapping_base['name']['analyzer'], 'lowercase')
