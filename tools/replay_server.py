
#!/usr/bbin/python2
# -*- coding: utf-8 -*-

# -- stdlib --
import sys
sys.path.append('../src')
import random
import gzip

import logging
logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger('ReplayServer')

from argparse import ArgumentParser

# -- third party --
import gevent
from gevent.queue import Queue
from gevent.event import Event
import simplejson as json

# -- own --
from game import autoenv
autoenv.init('Server')

from server.core import Player
from network import EndpointDied
from network.common import GamedataMixin
from account.freeplay import Account
from utils import BatchList


# -- code --
parser = ArgumentParser()
parser.add_argument('replay_file', type=str)
parser.add_argument('--catch', action='store_true')

options = parser.parse_args()


def ask_for_feed(player_index, tag):
    if not gdlist:
        log.warning('Game data exhausted.')
        if options.catch:
            import pdb; pdb.set_trace()

        sys.exit(0)

    data = gdlist[0]
    if tuple(data[:2]) == (player_index, tag):
        gdlist.pop(0)
        return data[1:]

    return None, GamedataMixin.NODATA

gdlist = []


class MockClient(object):
    def __init__(self, player_index):
        self.player_index = player_index
        self.account = Account.authenticate('Proton', '123')
        self.observers = []
        self._channel = Queue(0)
        e = Event()
        e.set()
        self.gdevent = e

    def gexpect(self, tag, blocking=True):
        assert not blocking
        data = ask_for_feed(self.player_index, tag)
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

if options.replay_file.endswith('.gz'):
    data = gzip.open(options.replay_file, 'r').read().split('\n')
else:
    data = open(options.replay_file, 'r').read().split('\n')

while data[0].startswith('#'):
    print data.pop(0)

mode = data.pop(0)
rndseed = long(data.pop(0))

gdlist = json.loads(data.pop(0))

from gamepack import gamemodes

mode = gamemodes[mode]

clients = [MockClient(i) for i in xrange(mode.n_persons)]
players = BatchList([Player(i) for i in clients])

g = mode()
g.players = players
g.rndseed = rndseed
g.random = random.Random(rndseed)
gevent.getcurrent().game = g
g._run()
