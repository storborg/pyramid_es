from unittest import TestCase

from ..result import ElasticResultRecord


class TestResult(TestCase):

    def _make_record(self):
        raw = {
            '_score': 0.85,
            '_id': 1234,
            '_type': 'Thing',
            '_source': {
                'name': 'Grue',
                'color': 'Dark'
            }
        }
        return ElasticResultRecord(raw)

    def test_record_repr(self):
        record = self._make_record()
        s = repr(record)
        self.assertIn('Thing', s)
        self.assertIn('1234', s)

    def test_record_getitem(self):
        record = self._make_record()
        self.assertEqual(record['_type'], 'Thing')

    def test_record_attr_source(self):
        record = self._make_record()
        self.assertEqual(record.name, 'Grue')

    def test_record_attr_raw(self):
        record = self._make_record()
        self.assertEqual(record._id, 1234)

    def test_record_attr_nonexistent(self):
        record = self._make_record()
        with self.assertRaises(AttributeError):
            record.nonexistent

    def test_record_contains(self):
        record = self._make_record()
        self.assertIn('_score', record)
        self.assertNotIn('foo', record)
