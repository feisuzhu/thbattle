# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
# -- own --


# -- code --
def extendclass(clsname, bases, _dict):
    for cls in bases:
        for key, value in _dict.items():
            if key == '__module__':
                continue
            setattr(cls, key, value)
