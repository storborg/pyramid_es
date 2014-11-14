from unittest import TestCase

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from sqlalchemy import Column, types
from sqlalchemy.ext.declarative import declarative_base
from six.moves.urllib.parse import urlencode

from webtest import TestApp

from .. import get_client
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


def index_view(request):
    es_client = get_client(request)
    es_client.refresh()
    result = es_client.query(Todo).execute()
    return {'todos': [rec._source for rec in result],
            'count': result.total}


def add_view(request):
    es_client = get_client(request)
    for s in request.params['description'].split(', '):
        todo = Todo(description=s)
        es_client.index_object(todo)
    if request.params.get('fail_after_index'):
        raise RuntimeError('fail!')
    return HTTPFound(location=request.route_url('index'))


def make_app():
    settings = {
        'elastic.index': 'pyramid_es_tests_app',
        'elastic.servers': ['localhost:9200'],
    }
    config = Configurator(settings=settings)
    config.include('pyramid_es')
    config.include('pyramid_tm')

    config.add_route('index', '/')
    config.add_view(index_view, route_name='index', renderer='json')

    config.add_route('add', '/add')
    config.add_view(add_view, route_name='add')

    es_client = get_client(config.registry)
    es_client.ensure_index(recreate=True)

    sample = Todo(description='Example to-do item')
    es_client.index_object(sample, immediate=True)

    return config.make_wsgi_app()


class TestPyramid(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = TestApp(make_app())

    def test_index(self):
        resp = self.app.get('/')
        resp.mustcontain('Example')

    def test_add_successful(self):
        params = urlencode({
            'description': 'Zygomorphic',
        })
        self.app.get('/add?' + params, status=302)
        # Check that new todo is now in the index.
        resp = self.app.get('/')
        resp.mustcontain('Zygomorphic')

    def test_add_fail(self):
        params = urlencode({
            'description': 'Nucleoplasm',
            'fail_after_index': True,
        })
        with self.assertRaises(RuntimeError):
            self.app.get('/add?' + params)

        resp = self.app.get('/')
        # Check that new todo is *not* in the index.
        self.assertNotIn('Nucleoplasm', resp.body.decode('utf8'))

    def test_add_alternate(self):
        params = urlencode({
            'description': 'Banana',
        })
        self.app.get('/add?' + params, status=302)
        resp = self.app.get('/')
        resp.mustcontain('Banana')

        params = urlencode({
            'description': 'Apple',
            'fail_after_index': 1,
        })
        with self.assertRaises(RuntimeError):
            self.app.get('/add?' + params)
        resp = self.app.get('/')
        self.assertNotIn('Apple', resp.body.decode('utf8'))

        params = urlencode({
            'description': 'Kiwi, Pineapple, Cherry',
        })
        self.app.get('/add?' + params, status=302)
        resp = self.app.get('/')
        resp.mustcontain('Kiwi')
