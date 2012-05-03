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
logging.getLogger().setLevel(logging.DEBUG)

from gevent.backdoor import BackdoorServer

gevent.spawn(BackdoorServer(('127.0.0.1', 10000)).serve_forever)

server = StreamServer(('0.0.0.0', 9999), Client.spawn, None)
server.serve_forever()
