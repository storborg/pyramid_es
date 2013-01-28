from unittest import TestCase

from pyramid.config import Configurator

from webtest import TestApp

from .data import Movie, get_data


def index_view(request):
    es_client = request.registry.es_client
    result = es_client.query(Movie).execute()
    return {'movies': [rec._source for rec in result],
            'count': result.count}


def make_app():
    settings = {
        'elastic.index': 'pyramid_es_tests',
        'elastic.servers': ['localhost:9200'],
    }
    config = Configurator(settings=settings)
    config.include('pyramid_es')

    config.add_route('index', '/')
    config.add_view(index_view, route_name='index', renderer='json')

    es_client = config.registry.es_client
    genres, movies = get_data()
    es_client.index_objects(movies)
    es_client.index_objects(genres)
    es_client.refresh()

    return config.make_wsgi_app()


class TestPyramid(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = TestApp(make_app())

    def test_index(self):
        resp = self.app.get('/')
        resp.mustcontain('Vertigo')
        self.assertEqual(resp.json['count'], 8)
