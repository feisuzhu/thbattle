# -*- coding: utf-8 -*-
import logging
import sys
import os
import argparse

reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

parser = argparse.ArgumentParser(prog=sys.argv[0])
parser.add_argument('--testing', action='store_true')
parser.add_argument('--no-update', action='store_true')
parser.add_argument('--with-gl-errcheck', action='store_true')
parser.add_argument('--freeplay', action='store_true')
parser.add_argument('--fastjoin', action='store_true')
parser.add_argument('--dump-gameobj', action='store_true')
parser.add_argument('--log', default='INFO')

options = parser.parse_args()

import options as opmodule
opmodule.options = options
IS_PROTON = hasattr(os, 'uname') and os.uname()[:2] == ('Linux', 'Proton')


class Tee(object):
    def __init__(self):
        self.logfile = f = open('client_log.txt', 'a')
        self.history = []
        import datetime
        s = (
            '\n' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") +
            '\n==============================================\n'
        )
        self.history.append(s)
        f.write(s)

    def write(self, v):
        sys.__stdout__.write(v)
        self.history.append(v)
        self.logfile.write(v.encode('utf-8'))

tee = sys.stderr = sys.stdout = Tee()

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(getattr(logging, options.log.upper()))

if IS_PROTON:
    from colorlog import ColoredFormatter

    formatter = ColoredFormatter(
        "%(log_color)s%(message)s%(reset)s",
        log_colors={
            'CRITICAL': 'bold_red',
            'ERROR': 'red',
            'WARNING': 'yellow',
            'INFO': 'green',
            'DEBUG': 'blue',
        }
    )

    logging.getLogger().handlers[0].setFormatter(formatter)

log = logging.getLogger('start_client')

# gevent: do not patch dns, they fail on windows
# monkey.patch_socket(dns=False) won't work since
# socket.create_connection internally references
# gevents' getaddrinfo
import socket
from gevent import socket as gsock

if not sys.platform.startswith('linux'):
    gsock.getaddrinfo = socket.getaddrinfo
    gsock.gethostbyname = socket.gethostbyname

    # HACK: resolve domain in parallel
    import threading

    class ResolveIt(threading.Thread):
        def __init__(self, host):
            threading.Thread.__init__(self)
            self.host = host

        def run(self):
            host = self.host
            socket.getaddrinfo(host, 80)
            socket.gethostbyname(host)

    domains = [
        'www.thbattle.net',
        'update.thbattle.net',
        'game.thbattle.net',
        'cngame.thbattle.net',
        'feisuzhu.xen.prgmr.com',
    ]
    for host in domains:
        thread = ResolveIt(host)
        thread.daemon = True
        thread.start()


from gevent import monkey
monkey.patch_socket()


from game import autoenv
autoenv.init('Client')

from client.core import Executive

import pyglet

pyglet.options['audio'] = ('directsound', 'openal', 'alsa', 'silent')
pyglet.options['shadow_window'] = False

if not options.with_gl_errcheck:
    pyglet.options['debug_gl'] = False

if sys.platform == 'win32':
    from pyglet.media.drivers.directsound import DirectSoundAudioPlayer
    DirectSoundAudioPlayer._buffer_size = 44800 * 2
    DirectSoundAudioPlayer._update_buffer_size = 44800 * 2 // 8

if sys.platform.startswith('linux') and options.dump_gameobj:
    import atexit
    import game
    atexit.register(game.GameObjectMeta._dump_gameobject_hierarchy)
    atexit.register(game.EventHandler._dump_eh_dependency_graph)


def do_crashreport():
    import requests
    import zlib
    import traceback

    import pyglet.info
    pyglet.info.dump()

    if not options.freeplay:
        s = u''.join(tee.history)
        s += u'\n\n' + traceback.format_exc()
        content = zlib.compress(s.encode('utf-8'))

        try:
            from game.autoenv import Game
            g = Game.getgame()
            gameid = g.gameid
        except:
            gameid = 0

        requests.post(
            'http://www.thbattle.net/interconnect/crashreport',
            data={'gameid': gameid}, files={'file': content},
        )


from client.ui.entry import start_ui

try:
    start_ui()
except:
    import pyglet
    pyglet.app.exit()

    if options.fastjoin:
        import pdb
        pdb.post_mortem()

    Executive.call('app_exit')
    log.error(u'游戏崩溃，正在报告bug，请稍等下……')
    do_crashreport()

    raise


if False and sys.platform == 'win32':
    import traceback

    def msgbox_error(exc_type, exc_value, exc_traceback):
        excstr = u"".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,  # HWND
            unicode(excstr),  # Text
            u'错误：请将这个截图并放到论坛的bug区里！',  # Caption
            16,  # Flags, MB_ICONERROR
        )

    traceback.print_exception = msgbox_error  # for greenlet failures
    sys.excepthook = msgbox_error


Executive.call('app_exit')
