from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging


def setUp():
    log = logging.getLogger('elasticsearch.trace')
    log.addHandler(logging.NullHandler())
