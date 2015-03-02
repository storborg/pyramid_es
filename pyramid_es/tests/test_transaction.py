from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from unittest import TestCase

import transaction
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base

from ..client import ElasticClient
from ..mixin import ElasticMixin, ESMapping, ESString


Base = declarative_base()


class Todo(Base, ElasticMixin):
    __tablename__ = 'todos'
    id = Column(types.Integer, primary_key=True)
    description = Column(types.Unicode(40))

    @classmethod
    def elastic_mapping(cls):
        return ESMapping(
            analyzer='content',
            properties=ESMapping(
                ESString('description', boost=5.0)))


class TestClient(TestCase):

    def setUp(self):
        self.client = ElasticClient(servers=['localhost:9200'],
                                    index='pyramid_es_tests_txn',
                                    use_transaction=True)
        self.client.ensure_index(recreate=True)
        self.client.ensure_mapping(Todo)

    def test_index_and_delete_document(self):
        todo = Todo(id=42, description='Finish exhaustive test suite')

        with transaction.manager:
            self.client.index_object(todo)
        self.client.flush(force=True)
        self.client.refresh()

        # Search for this document and make sure it exists.
        q = self.client.query(Todo, q='exhaustive')
        result = q.execute()
        todos = [doc.description for doc in result]
        self.assertIn('Finish exhaustive test suite', todos)

        with transaction.manager:
            self.client.delete_object(todo)

        self.client.flush(force=True)
        self.client.refresh()

        # Search for this document and make sure it DOES NOT exist.
        q = self.client.query(Todo, q='exhaustive')
        result = q.execute()
        todos = [doc.description for doc in result]
        self.assertNotIn('Finish exhaustive test suite', todos)
