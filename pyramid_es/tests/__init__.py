import logging


def setUp():
    log = logging.getLogger('elasticsearch.trace')
    log.setLevel(logging.CRITICAL)
