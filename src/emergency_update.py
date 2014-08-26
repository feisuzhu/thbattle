# - * - coding: utf-8 - * -

import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

import autoupdate
import settings


def cb(*a):
    print a

import socket
from gevent import socket as gsock

if not sys.platform.startswith('linux'):
    gsock.getaddrinfo = socket.getaddrinfo
    gsock.gethostbyname = socket.gethostbyname

import gevent
from gevent import monkey
monkey.patch_socket()

rst = gevent.spawn(autoupdate.do_update, settings.UPDATE_BASE, settings.EMERGENCY_UPDATE_URL, cb).get()

print 'Result:', rst
