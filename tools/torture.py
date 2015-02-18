#!/usr/bin/python2
# -*- coding: utf-8 -*-

# -- stdlib --
import itertools

# -- third party --
from gevent import socket
import gevent
import msgpack

# -- own --
# -- code --
names = ['Reimu', 'Marisa', 'Sakuya', 'Youmu', 'Sanae', 'Yuyuko', 'Alice', 'Patchouli']
names = itertools.cycle(names)


def en(d):
    return msgpack.packb([1, d])


def create():
    s = socket.socket()
    s.connect(('127.0.0.1', 9999))
    s.sendall(en(['auth', [names.next(), '']])); gevent.sleep(0.05)
    s.sendall(en(['create_game', ['THBattleIdentity', u'我们是机器人哈哈哈']])); gevent.sleep(0.05)
    s.sendall(en(['get_ready', []])); gevent.sleep(0.05)
    return s


def join():
    s = socket.socket()
    s.connect(('127.0.0.1', 9999))
    s.sendall(en(['auth', [names.next(), '']])); gevent.sleep(0.05)
    s.sendall(en(['quick_start_game', []])); gevent.sleep(0.05)
    s.sendall(en(['get_ready', []])); gevent.sleep(0.05)
    return s


def torture():
    l = []
    print 'create'
    l.append(create())

    gevent.sleep(2.0)

    print 'join'
    for i in xrange(8):
        l.append(join())

    print 'done'

    for _ in xrange(3):
        for s in l:
            s.recv(1000)
        gevent.sleep(3)

    for s in l:
        s.close()

from gevent.pool import Pool

pool = Pool(300)

for i in xrange(30000):
    pool.spawn(torture)

pool.join()
