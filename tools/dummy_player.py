#!/usr/bin/python2
# -*- coding: utf-8 -*-

import gevent
from gevent import socket
from simplejson import dumps

names = ['Reimu', 'Marisa', 'Sakuya', 'Youmu', 'Sanae', 'Yuyuko', 'Alice', 'Patchouli']
import itertools
names = itertools.cycle(names)

import sys

types = {
    '3v3': 'THBattle',
    'id5': 'THBattleIdentity5',
    'id8': 'THBattleIdentity',
    'kof': 'THBattleKOF',
    'raid': 'THBattleRaid',
    'faith': 'THBattleFaith',
}

argv = sys.argv[1:]
t = argv.pop(0)
n = int(argv.pop(0))
N = int(argv.pop(0)) if argv else 1

t = types[t]
no_create = n < 0
n = abs(n)

en = lambda d: dumps(d) + '\n'

l = []


def create():
    s = socket.socket()
    s.connect(('127.0.0.1', 9999))
    s.sendall(en(['auth', [names.next(), '']])); gevent.sleep(0.05)
    s.sendall(en(['create_game', [t, u'我们是机器人哈哈哈']])); gevent.sleep(0.05)
    s.sendall(en(['get_ready', None])); gevent.sleep(0.05)

    while s.recv(100): pass


def join():
    s = socket.socket()
    s.connect(('127.0.0.1', 9999))
    s.sendall(en(['auth', [names.next(), '']])); gevent.sleep(0.05)
    s.sendall(en(['quick_start_game', 'nyan'])); gevent.sleep(0.05)
    s.sendall(en(['get_ready', None])); gevent.sleep(0.05)

    while s.recv(100): pass


if not no_create:
    print 'create'
    for _ in xrange(int(N)):
        l.append(gevent.spawn(create))

    gevent.sleep(1.0)

print 'join'
for _ in xrange(int(N)):
    for i in xrange(n-(not no_create)):
        l.append(gevent.spawn(join))

print 'done'

# import signal
# signal.alarm(2)

for i in l:
    i.join()
