# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from gevent import subprocess

# -- own --
from utils.misc import flatten


# -- code --
def _do_open_dlg(window, title, filters, extra):
    args = ['zenity', '--file-selection', '--title', title] + extra
    args += flatten([('--file-filter', u'|'.join(i)) for i in filters])
    handle = subprocess.Popen(args, stdout=subprocess.PIPE)
    return handle.stdout.read().strip()


def get_open_file_name(window, title, filters):
    return _do_open_dlg(window, title, filters, [])


def get_save_file_name(window, title, filters):
    return _do_open_dlg(window, title, filters, ['--save'])
