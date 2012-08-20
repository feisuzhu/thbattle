import gevent
from gevent.server import StreamServer
from server.core import Client

import logging
import sys

'''
# --- for dbg
from gevent import signal as sig
import signal
sig(signal.SIGUSR1, lambda: False)
# -----------
'''

from game import autoenv
autoenv.init('Server')

from network import Endpoint
#Endpoint.ENDPOINT_DEBUG = True

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.INFO)

from gevent.backdoor import BackdoorServer

if len(sys.argv) > 1 and sys.argv[1] == 'TESTING':
    gameport, bdport = 9998, 10001
else:
    gameport, bdport = 9999, 10000

gevent.spawn(BackdoorServer(('127.0.0.1', bdport)).serve_forever)

server = StreamServer(('0.0.0.0', gameport), Client.spawn, None)
server.serve_forever()
