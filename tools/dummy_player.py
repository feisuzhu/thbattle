#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -- stdlib --
import itertools
import sys

# -- third party --
from gevent import socket
import gevent
import msgpack

# -- own --
# -- code --
names = range(3, 14)
names = itertools.cycle(names)
types = {
    '3v3':   'THBattle',
    'cp3':   'THBattleCP3',
    'id5':   'THBattleIdentity5',
    'id8':   'THBattleIdentity',
    'kof':   'THBattleKOF',
    'raid':  'THBattleRaid',
    'faith': 'THBattleFaith',
    '2v2':   'THBattle2v2',
    'book':  'THBattleBook',
}

argv = sys.argv[1:]
t = argv.pop(0)
n = int(argv.pop(0))
N = int(argv.pop(0)) if argv else 1

t = types[t]
no_create = n < 0
n = abs(n)

# en = lambda d: dumps(d) + '\n'


def en(d):
    return msgpack.packb([1, d])


l = []


def create():
    s = socket.socket()
    s.connect(('127.0.0.1', 9999))
    s.sendall(en(['auth', [names.next(), 'feisuzhu']])); gevent.sleep(0.05)
    s.sendall(en(['lobby', ['create_game', [t, u'我们是机器人哈哈哈', False]]])); gevent.sleep(0.05)
    s.sendall(en(['lobby', ['get_ready', []]])); gevent.sleep(0.05)

    while s.recv(100): pass


def join():
    s = socket.socket()
    s.connect(('127.0.0.1', 9999))
    s.sendall(en(['auth', [names.next(), 'feisuzhu']])); gevent.sleep(0.05)
    s.sendall(en(['lobby', ['quick_start_game', []]])); gevent.sleep(0.05)
    s.sendall(en(['lobby', ['get_ready', []]])); gevent.sleep(0.05)
    while True:
        gevent.sleep(5)
        s.sendall(en(['heartbeat', []]))
        s.recv(100)


if not no_create:
    print 'create'
    for _ in xrange(int(N)):
        l.append(gevent.spawn(create))

    gevent.sleep(2.0)

print 'join'
for _ in xrange(int(N)):
    for i in xrange(n-(not no_create)):
        l.append(gevent.spawn(join))

print 'done'

# import signal
# signal.alarm(2)

for i in l:
    i.join()
