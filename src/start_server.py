import gevent
from gevent.server import StreamServer

import logging
import sys

'''
# --- for dbg
from gevent import signal as sig
import signal
sig(signal.SIGUSR1, lambda: False)
# -----------
'''

main = gevent.getcurrent()

from gevent import signal as sig
import signal

def _exit_handler(*a, **k):
    gevent.kill(main, SystemExit)
sig(signal.SIGTERM, _exit_handler)

from game import autoenv

import argparse

parser = argparse.ArgumentParser(prog=sys.argv[0])
parser.add_argument('--port', default=9999, type=int)
parser.add_argument('--backdoor-port', default=10000, type=int)
parser.add_argument('--testing', action='store_true')
parser.add_argument('--no-backdoor', action='store_true')
parser.add_argument('--freeplay', action='store_true')
parser.add_argument('--conf')
parser.add_argument('--log', default='INFO')
parser.add_argument('--logfile', default='')
parser.add_argument('--gidfile', default='')
parser.add_argument('--archive-path', default='')

options = parser.parse_args()

import options as opmodule

opmodule.options = options

autoenv.init('Server')

import settings

if options.conf:
    import os
    with open(options.conf, 'r') as f:
        src = f.read()
    env = {}
    exec src in env
    for k, v in env.items():
        setattr(settings, k, v)

from network import Endpoint
#Endpoint.ENDPOINT_DEBUG = True

class ServerLogFormatter(logging.Formatter):
    def format(self, rec):
        
        if rec.exc_info:
            s = []
            s.append('>>>>>>' + '-' * 74)
            s.append(self._format(rec))
            import traceback
            s.append(u''.join(traceback.format_exception(*sys.exc_info())).strip())
            s.append('<<<<<<' + '-' * 74)
            return u'\n'.join(s)
        else:
            return self._format(rec)

    def _format(self, rec):
        from game.autoenv import Game
        import time
        try:
            g = Game.getgame()
        except:
            g = gevent.getcurrent()

        return u'[%s %s %s] %s' % (
            rec.levelname[0],
            time.strftime('%y%m%d %H:%M:%S'),
            repr(g).decode('utf-8'),
            rec.msg % rec.args,
        )


fmter = ServerLogFormatter()

root = logging.getLogger()

root.setLevel(getattr(logging, options.log.upper()))
std = logging.StreamHandler(stream=sys.stdout)
std.setFormatter(fmter)
root.addHandler(std)

if options.logfile:
    from logging.handlers import WatchedFileHandler
    filehdlr = WatchedFileHandler(options.logfile)
    filehdlr.setFormatter(fmter)
    root.addHandler(filehdlr)

if not options.no_backdoor:
    from gevent.backdoor import BackdoorServer
    gevent.spawn(BackdoorServer(('127.0.0.1', options.backdoor_port)).serve_forever)

from server.core import Client
from custom_options import options
options.default('server_startup', None)
exec unicode(options.server_startup)

root.info('=' * 20 + settings.VERSION + '=' * 20)
server = StreamServer(('0.0.0.0', options.port), Client.spawn, None)
server.serve_forever()
