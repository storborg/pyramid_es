class DotDict(dict):

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, d={}):
        for key, value in d.items():
            if hasattr(value, 'keys'):
                value = DotDict(value)
            self[key] = value

    def __repr__(self):
        return '<DotDict(%s)>' % dict.__repr__(self)
