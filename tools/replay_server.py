# -*- coding: utf-8 -*-

# -- prioritized --
from game import autoenv
autoenv.init('Server')

# -- stdlib --
from argparse import ArgumentParser
from weakref import WeakSet
import gzip
import json
import logging
import random
import sys

# -- third party --
from gevent.event import Event
from gevent.queue import Queue
import gevent

# -- own --
from account.freeplay import Account
from endpoint import EndpointDied
from game import Gamedata
from server.core import Player, NPCPlayer, NPCClient
from utils import BatchList

# -- code --
logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger('ReplayServer')

parser = ArgumentParser()
parser.add_argument('replay_file', type=str)
parser.add_argument('--catch', action='store_true')

options = parser.parse_args()


def ask_for_feed(player_index, tag):
    if not gdlist:
        log.warning('Game data exhausted.')
        if options.catch:
            import pdb
            pdb.set_trace()

        sys.exit(0)

    data = gdlist[0]
    if tuple(data[:2]) == (player_index, tag):
        gdlist.pop(0)
        return data[1:]
    elif (player_index, tag) not in gdlist_tag:
        return EndpointDied
    else:
        return None, Gamedata.NODATA

gdlist = []
gdlist_tag = set()


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
        while True:
            data = ask_for_feed(self.player_index, tag)
            if data is EndpointDied:
                raise EndpointDied

            if data == (None, Gamedata.NODATA):
                gevent.sleep(0.1)  # just poll
                continue

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
params = json.loads(data.pop(0))
rndseed = long(data.pop(0))

gdlist = json.loads(data.pop(0))
gdlist_tag = set(tuple(i[:2]) for i in gdlist)
print gdlist_tag

from gamepack import gamemodes

mode = gamemodes[mode]

clients = [MockClient(i) for i in xrange(mode.n_persons)]
players = BatchList([Player(i) for i in clients])
players[:0] = [NPCPlayer(NPCClient(i.name), i.input_handler) for i in mode.npc_players]

g = mode()
g.players = players
g.rndseed = rndseed
g.synctag = 0
g.random = random.Random(rndseed)
g.game_params = params
g.gr_groups = WeakSet()
g.game = g
g.pause = lambda x: None
gevent.getcurrent().game = g
g.game_start(params)
