class DotDict(dict):
    """
    A utility class which behaves like a dict, but also allows dot-access of
    keys. When instantiated from a source dict, the source will be recursively
    crawled to convert sub-dicts to this class, as well.
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, d={}):
        for key, value in d.items():
            if hasattr(value, 'keys'):
                value = DotDict(value)
            if isinstance(value, list):
                value = [DotDict(el) if hasattr(el, 'keys') else el
                         for el in value]
            self[key] = value

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, dict.__repr__(self))
