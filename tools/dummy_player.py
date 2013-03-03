#!/usr/bbin/python2
# -*- coding: utf-8 -*-

import gevent
from gevent import socket
from simplejson import dumps

names = ['Reimu', 'Marisa', 'Sakuya', 'Youmu', 'Sanae', 'Yuyuko', 'Alice', 'Patchouli']
import itertools
names = itertools.cycle(names)

import sys

types = [
    ('THBattle', 5), # 0
    ('THBattle', 6), # 1
    ('THBattle', 4),  # 2
    ('THBattleIdentity5', 5), # 3
    ('THBattleIdentity', 7), # 4
    ('THBattleKOF', 2), # 5
    ('THBattleRaid', 4), # 6
    ('THBattleRaid', -3), # 7
    ('THBattleRaid', 2), # 8
]

t, N = sys.argv[1:]
t, n = types[int(t)]
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

for i in l:
    i.join()
