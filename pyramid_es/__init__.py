from .client import ElasticClient


def client_from_config(settings, prefix='elastic.'):
    return ElasticClient(
        servers=settings.get(prefix + 'servers', ['localhost:9200']),
        timeout=settings.get(prefix + 'timeout', 1.0),
        index=settings[prefix + 'index'],
        disable_indexing=settings.get(prefix + 'disable_indexing', False))


def includeme(config):
    registry = config.registry
    settings = registry.settings

    client = client_from_config(settings)
    client.ensure_index()

    registry.pyramid_es_client = client


def get_client(request):
    registry = getattr(request, 'registry', None)
    if registry is None:
        registry = request
    return registry.pyramid_es_client
