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
parser.add_argument('--conf')

options = parser.parse_args()

import options as opmodule

opmodule.options = options

autoenv.init('Server')

if options.conf:
    import os
    with open(options.conf, 'r') as f:
        src = f.read()
    import settings
    env = {}
    exec src in env
    for k, v in env.items():
        setattr(settings, k, v)

from network import Endpoint
#Endpoint.ENDPOINT_DEBUG = True

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.INFO)

if not options.no_backdoor:
    from gevent.backdoor import BackdoorServer
    gevent.spawn(BackdoorServer(('127.0.0.1', options.backdoor_port)).serve_forever)

from server.core import Client

server = StreamServer(('0.0.0.0', options.port), Client.spawn, None)
server.serve_forever()
