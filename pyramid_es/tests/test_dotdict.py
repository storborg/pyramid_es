from unittest import TestCase

from ..dotdict import DotDict


class TestDotDict(TestCase):
    def test_get(self):
        dd = DotDict({'a': 42,
                      'b': 'hello'})
        self.assertEqual(dd['b'], 'hello')
        self.assertEqual(dd.b, 'hello')

    def test_recursive(self):
        dd = DotDict({'a': 42,
                      'b': {'one': 1,
                            'two': 2,
                            'three': 3}})
        self.assertEqual(dd['b']['two'], 2)
        self.assertEqual(dd.b.two, 2)

    def test_set(self):
        dd = DotDict({'a': 4,
                      'b': 9})
        dd.c = 16
        self.assertEqual(dd.c, 16)
        self.assertEqual(dd['c'], 16)

    def test_del(self):
        dd = DotDict({'a': 123,
                      'b': 456})
        del dd.b
        self.assertEqual(dict(dd), {'a': 123})
