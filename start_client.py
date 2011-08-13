import G; G.RUNNING = 'Client'
from utils import ITIHub,ITIEvent; ITIHub.replace_default()
from client.core import GameManager
import threading

from gevent import socket
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


gm = GameManager()
G.gm = gm

log.debug("connect to server")

server = gm.connect(('127.0.0.1', 9999)).get()
gm.heartbeat()
gm.inroom_handler()

myid = gm.auth('proton', 'password').get()

class InputThread(threading.Thread):
    def run(self):
        import time
        while True:
            global s, se
            print 'Cmd: ',
            ss = raw_input()
            if ss == '1':
                ss = 'create_game,Simple Game'
            elif ss == '2':
                ss = 'quick_start_game'
            elif ss == '3':
                ss = 'get_ready'
            ss = ss.split(',')
            if len(ss) == 1:
                ss.append(None)
            s = ss
            se.set()
            time.sleep(0.1)

InputThread().start()

while True:
    se.wait()
    server.write(s)
    se.clear()
