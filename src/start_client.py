# -*- coding: utf-8 -*-
import threading
import logging, sys
import argparse

reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

parser = argparse.ArgumentParser(prog=sys.argv[0])
parser.add_argument('--testing', action='store_true')
parser.add_argument('--no-update', action='store_true')
parser.add_argument('--with-gl-errcheck', action='store_true')
parser.add_argument('--freeplay', action='store_true')

options = parser.parse_args()

import options as opmodule
opmodule.options = options

from utils import hook

class Tee(object):
    def __init__(self):
        self.logfile = f = open('client_log.txt', 'a')
        import datetime
        f.write(
            '\n' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") +
            '\n==============================================\n'
        )

    def write(self, v):
        sys.__stdout__.write(v)
        self.logfile.write(v.encode('utf-8'))

sys.stderr = sys.stdout = Tee()

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger('__main__')

import gevent
from gevent import monkey
monkey.patch_socket()

from gevent import socket, dns

@hook(socket)
def getaddrinfo(ori, host, port, family=0, socktype=0, proto=0, flags=0):
    while True:
        try:
            # WARNING:
            # Don't change the 'family'!
            # gevent 0.13 on Windows doesn't handle IPv6 well!
            return ori(host, port, socket.AF_INET, socktype, proto, flags)
        except dns.DNSError as e:
            if not e.errno == 2: # dns server fail thing
                raise
        gevent.sleep(0.15)

@hook(socket)
def gethostbyname(ori, hostname):
    while True:
        try:
            return ori(hostname)
        except dns.DNSError as e:
            if not e.errno == 2: # dns server fail thing
                raise
        gevent.sleep(0.15)

# -----------------------------------------

from game import autoenv
autoenv.init('Client')

from client.core import Executive

# for dbg
'''
from gevent import signal as gsig
import signal
def print_stack():
    game = Executive.gm_greenlet.game
    import traceback
    traceback.print_stack(game.gr_frame)
gsig(signal.SIGUSR1, print_stack)
# -------
'''


import pyglet

pyglet.options['audio'] = ('directsound', 'openal', 'alsa', 'silent')
pyglet.options['shadow_window'] = False
# pyglet.options['graphics_vbo'] = False  # AMD: Do you have QA team for your OpenGL driver ????

if not options.with_gl_errcheck:
    pyglet.options['debug_gl'] = False

if sys.platform == 'win32':
    from pyglet.media.drivers.directsound import DirectSoundAudioPlayer
    DirectSoundAudioPlayer._buffer_size = 44800 * 2
    DirectSoundAudioPlayer._update_buffer_size = 44800 * 2 // 8

from client.ui.entry import start_ui

try:
    start_ui()
except:
    import traceback
    traceback.print_exc()
    import pyglet
    pyglet.app.exit()

Executive.call('app_exit')
