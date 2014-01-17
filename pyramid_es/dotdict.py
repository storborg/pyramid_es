class DotDict(dict):

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
