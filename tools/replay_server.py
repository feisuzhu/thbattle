
#!/usr/bbin/python2
# -*- coding: utf-8 -*-

import sys
sys.path.append('../src')

import random
import gevent
from gevent import Greenlet
from gevent.queue import Queue

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
parser.add_argument('--break', type=int, default=0)

options = parser.parse_args()


class DataSource(Greenlet):
    def __init__(self, gdlist):
        Greenlet.__init__(self)
        self.gdlist = gdlist
        self.channel = Queue(100000)
        indexes = [i[0] for i in gdlist]
        cnt = [indexes.count(i) for i in xrange(10)]
        self.data_count = cnt

    def _run(self):
        cnt = self.data_count
        data = self.gdlist.pop(0)
        for idx, tag, retchannel in self.channel:
            if not self.gdlist or not cnt[idx]:
                retchannel.put(EndpointDied)

            if tuple(data[:2]) == (idx, tag):
                retchannel.put(data[2])
                data = self.gdlist.pop(0)
            else:
                log.info('!! Req:%s, Has:%s', repr((idx, tag)), repr(data[:2]))
                self.channel.put((idx, tag, retchannel))

    def ask_for_feed(self, player_index, tag, retchannel):
        self.channel.put((player_index, tag, retchannel))
        return retchannel.get()


class MockClient(object):
    def __init__(self, player_index, datasource):
        self.player_index = player_index
        self.datasource = datasource
        self.account = Account.authenticate('Proton', '123')
        self.observers = []
        self._channel = Queue(0)

    def gexpect(self, tag):
        data = self.datasource.ask_for_feed(self.player_index, tag, self._channel)
        if data is EndpointDied:
            raise EndpointDied
        log.info('GAME_EXPECT[%d]: %s, return %s', self.player_index, repr(tag), repr(data))
        return data

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE[%d]: %s', self.player_index, repr([tag, data]))

    def write(self, data):
        pass

    def gclear(self):
        pass


data = open(options.replay_file, 'r').read().split('\n')

while data[0].startswith('#'):
    print data.pop(0)

mode = data.pop(0)
rndseed = long(data.pop(0))

gdlist = json.loads(data.pop(0))

datasource = DataSource(gdlist)
datasource.start()

from gamepack import gamemodes

mode = gamemodes[mode]

clients = [MockClient(i, datasource) for i in xrange(mode.n_persons)]
players = PlayerList([Player(i) for i in clients])

g = mode()
g.players = players
g.rndseed = rndseed
g.random = random.Random(rndseed)
gevent.getcurrent().game = g
g._run()
