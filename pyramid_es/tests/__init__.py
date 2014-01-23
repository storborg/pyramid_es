import logging


def setUp():
    log = logging.getLogger('elasticsearch.trace')
    log.addHandler(logging.NullHandler())
