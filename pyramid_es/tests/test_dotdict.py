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

    def test_recursive_list(self):
        dd = DotDict({
            'organization': 'Avengers',
            'members': [
                {'id': 1, 'name': 'Bruce Banner'},
                {'id': 2, 'name': 'Tony Stark'},
                {'id': 3, 'name': 'Steve Rogers'},
                {'id': 4, 'name': 'Natasha Romanoff'}
            ]
        })
        self.assertEqual(dd.members[1].name, 'Tony Stark')

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

    def test_repr(self):
        dd = DotDict({'a': 1})
        self.assertEqual(repr(dd), "<DotDict({'a': 1})>")
