import sys
import os

sys.path.append(os.path.dirname(os.getcwd()))

from gevent import socket
from network import *
import simplejson as json
import sys

so = socket.socket()
so.connect(('127.0.0.1', 9999))

s = Endpoint.spawn(so, '127.0.0.1')

def write(d):
    sys.stdout.write('>> %s' % s.encode(d))
    s.write(d)

def heartbeat():
    while True:
        gevent.sleep(15)
        write(['heartbeat', None])

def recv():
    while True:
        r = s.encode(s.read())
        sys.stdout.write('<< %s' % r)

def stall(t=1):
    gevent.sleep(t)

gevent.spawn(heartbeat)
gevent.spawn(recv)

write(['auth',['feisuzhu', 'Proton']])
stall()
write(['create_game','A Dummy Game'])
stall()
stall()
write(['list_game', None])
stall()
write(['get_ready', None])
stall()

stall(500)
