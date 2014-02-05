from unittest import TestCase

from ..result import ElasticResult, ElasticResultRecord


sample_record1 = {
    '_score': 0.85,
    '_id': 1234,
    '_type': 'Thing',
    '_source': {
        'name': 'Grue',
        'color': 'Dark'
    }
}


sample_record2 = {
    '_score': 0.62,
    '_id': 1249,
    '_type': 'Thing',
    '_source': {
        'name': 'Widget',
        'color': 'Red'
    }
}


sample_result = {
    u'_shards': {
        u'failed': 0,
        u'successful': 2,
        u'total': 2
    },
    u'hits': {
        u'hits': [
            sample_record1,
            sample_record2,
        ],
        u'max_score': 0.85,
        u'total': 2
    },
    u'timed_out': False,
    u'took': 1
}


class TestResult(TestCase):

    def _make_result(self):
        return ElasticResult(sample_result)

    def test_result_repr(self):
        result = self._make_result()
        self.assertIn('total:2', repr(result))


class TestResultRecord(TestCase):

    def _make_record(self):
        return ElasticResultRecord(sample_record1)

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
