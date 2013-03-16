# -*- coding: utf-8 -*-

class options(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, value):
        return self.store(name, value)

    def store(self, name, value):
        self[name] = value
        import os.path
        path = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(path, 'options_custom.py'), 'w')
        try:
            f.write('from custom_options import options\n')
            f.write('options.load(')
            f.write(repr(self))
            f.write(')\n')
        finally:
            f.close()

    def default(self, name, default):
        if name not in self:
            self[name] = default

    def load(self, data):
        self.update(data)

options = options()

try:
    import options_custom
except:
    pass
