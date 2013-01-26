from .client import ElasticClient


def includeme(config):
    registry = config.registry
    settings = registry.settings

    client = ElasticClient(
        servers=settings.get('elastic.servers', ['localhost:9200']),
        timeout=settings.get('elastic.timeout', 1.0),
        index=settings.get('elastic.index', registry.__name__),
        disable_indexing=settings.get('elastic.disable_indexing', False))

    client.ensure_index()

    registry.es_client = client
