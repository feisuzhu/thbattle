from utils import ITIHub,ITIEvent; ITIHub.replace_default()

from game import autoenv
autoenv.init('Client')

from client.core import Executive
import threading

from gevent import socket
from gevent.event import Event
import gevent

from network import Endpoint
Endpoint.ENDPOINT_DEBUG = True

import logging
import sys

s = ''
se = ITIEvent()

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger('__main__')

gevent.spawn(Executive.run)

log.debug("connect to server")

evt = Event()

def signalit(*args, **kwargs):
    global evt
    print args, kwargs
    evt.set()

evt.clear()
Executive.message('connect_server', signalit, ('127.0.0.1', 9999))
print 'wait1'
evt.wait()
print 'wait2'

evt.clear()
Executive.message('authenticate', signalit, 'proton', 'password')
evt.wait()

server = Executive.server

if sys.argv[1] == '1':
    server.write(['create_game','Simple Game'])
    server.write(['get_ready', None])
elif sys.argv[1] == '2':
    server.write(['quick_start_game', None])
    server.write(['get_ready', None])
    
server.join()
