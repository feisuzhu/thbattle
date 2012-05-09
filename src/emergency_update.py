# - * - coding: utf-8 - * -

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

import autoupdate
import settings

def cb(*a):
    print a

import gevent
rst = gevent.spawn(autoupdate.do_update, settings.UPDATE_BASE, settings.UPDATE_URL, cb).get()

print 'Result:', rst
