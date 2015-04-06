# -*- coding: utf-8 -*-

# -- stdlib --
from functools import partial
import sys

# -- third party --
import gevent

# -- own --
# -- code --
__all__ = [
    'get_open_file_name',
    'get_save_file_name',
]

if sys.platform == 'win32':
    from .win32 import get_open_file_name as win32_gofn, get_save_file_name as win32_gsfn

    def _do_open(func, window, title, filters):
        rst = gevent.get_hub().threadpool.spawn(func, window, title, filters)
        return rst.get()

    get_open_file_name = partial(_do_open, win32_gofn)
    get_save_file_name = partial(_do_open, win32_gsfn)

elif sys.platform.startswith('linux'):
    from .zenity import get_open_file_name, get_save_file_name  # noqa

else:
    def get_open_file_name(*a):
        return None

    def get_save_file_name(*a):
        return None
