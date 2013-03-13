
#!/usr/bbin/python2
# -*- coding: utf-8 -*-

import sys
sys.path.append('../src')

import random
import gevent

from game import autoenv
autoenv.init('Server')

from game.autoenv import Game
from server.core import Player, PlayerList

from network import EndpointDied

from account.freeplay import Account

import simplejson as json

import logging
logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger('ReplayServer')


from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('replay_file', type=str)

options = parser.parse_args()


class Counter(object):
    def __init__(self, v):
        self.v = v

    def dec(self):
        self.v -= 1
        if not self.v:
            log.info('Counter down')
            sys.exit(0)


class MockClient(object):
    def __init__(self, gdlist, counter):
        self.gdlist = gdlist
        self.account = Account.authenticate('Proton', '123')
        self.counter = counter
        self.observers = []

    def gexpect(self, tag):
        if not self.gdlist or self.dropped:
            raise EndpointDied

        data = self.gdlist.pop(0)
        log.info('GAME_EXPECT: %s, return %s', repr(tag), repr(data))
        print 'GAME_EXPECT: %s, return %s', repr(tag), repr(data)
        import gevent

        if not self.gdlist:
            log.info('Player data exhausted.')
            self.dropped = True
            self.counter.dec()

        return data

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))

    def write(self, data):
        pass

    def gclear(self):
        pass


data = open(options.replay_file, 'r').read().split('\n')
print data.pop(0)
print data.pop(0)
mode = data.pop(0)
rndseed = long(data.pop(0))

print mode, rndseed, data
sys.exit(0)

from gamepack import gamemodes

mode = gamemodes[mode]

assert len(data) == mode.n_persons

counter = Counter(mode.n_persons)

clients = [MockClient(json.loads(i), counter) for i in data]
players = PlayerList([Player(i) for i in clients])

g = mode()
g.players = players
g.rndseed = rndseed
g.random = random.Random(rndseed)
gevent.getcurrent().game = g
g._run()

