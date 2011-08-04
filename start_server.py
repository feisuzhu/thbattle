import gevent
from gevent.server import StreamServer
from server.core import Client

import logging
import sys

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.DEBUG)

server = StreamServer(('0.0.0.0', 9999), Client.spawn, None)
server.serve_forever()

