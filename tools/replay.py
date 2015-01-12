# -*- coding: utf-8 -*-

# -- prioritized --
import sys
sys.path.append('../src')
from game import autoenv
autoenv.init('Client')
from game.autoenv import Game
Game.CLIENT_SIDE = 'blah'  # Hack: not loading ui resource

# -- stdlib --
from argparse import ArgumentParser
import gzip
import json
import logging
import pdb

# -- third party --
# -- own --
from account.freeplay import Account
from client.core import PeerPlayer, TheLittleBrother
from gamepack import gamemodes
from utils import BatchList, hook

# -- code --
parser = ArgumentParser()
parser.add_argument('replay_file', type=str)
parser.add_argument('location', type=int)
parser.add_argument('--catch', action='store_true', default=False)
parser.add_argument('--log', type=str, default='DEBUG')
parser.add_argument('--break-at', type=int, default=0)
parser.add_argument('--print-synctag', action='store_true', default=False)
parser.add_argument('--action-singlestep', default=0)
options = parser.parse_args()

logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(getattr(logging, options.log.upper()))
log = logging.getLogger('Replay')


class MockExecutive(object):
    def __init__(self, server):
        self.server = server
        self.account = Account.authenticate('Proton', '123')


class MockServer(object):
    def __init__(self, gdlist):
        self.gdlist = gdlist

    def gexpect(self, tag):
        log.info('GAME_EXPECT: %s', repr(tag))
        if not self.gdlist:
            log.info('Game data exhausted, exiting...')
            if options.catch:
                import pdb; pdb.set_trace()
            sys.exit(0)

        glob = False
        if tag.endswith('*'):
            tag = tag[:-1]
            glob = True

        missed = False
        for i, d in enumerate(self.gdlist):
            if d[0] == tag or (glob and d[0].startswith(tag)):
                log.info('GAME_READ: %s', repr(d))
                del self.gdlist[i]
                return d
            if not missed:
                log.info('GAME_DATA_MISS: %s', repr(d))
                missed = True

        log.info('GAME_DATA_MISS!!')
        log.info('Remaining game data:')
        for i in self.gdlist:
            log.info(repr(i))

        sys.exit(1)

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))

    def gclear(self):
        pass


if options.replay_file.endswith('.gz'):
    data = gzip.open(options.replay_file, 'r').read()
else:
    data = open(options.replay_file, 'r').read()

data = data.split('\n')

while True:
    last = data.pop(0)
    if not last.startswith('#'):
        break
    print last

mode = last
params = json.loads(data.pop(0))
data.pop(0)  # seed
data.pop(0)  # server data

loc = options.location
gdlist = json.loads(data.pop(0))[loc]

server = MockServer(gdlist)
Executive = MockExecutive(server)

from client.core import game_client
game_client.Executive = Executive  # Hack

GameMode = gamemodes[mode]

players = [PeerPlayer() for i in xrange(GameMode.n_persons)]
players[loc].__class__ = TheLittleBrother
players[loc].server = server

for p in players:
    p.account = Account.authenticate('Proton', '123')

g = GameMode()
g.players = BatchList(players)
g.game_params = params
g.me = players[loc]
g.replay_file = options.replay_file


@hook(g)
def pause(*a):
    pass


@hook(g)
def get_synctag(ori):
    tag = ori()
    if options.print_synctag:
        print '----- %d -----' % tag

    if options.break_at and tag == options.break_at:
        if options.catch:
            pdb.set_trace()
        else:
            raise Exception('break!')

    return tag


@hook(g)
def process_action(ori, act):
    ass = options.action_singlestep
    if ass and ass >= g.synctag:
        print g.action_stack
        raw_input()

    return ori(act)

try:
    g._run()
except Exception as e:
    if not isinstance(e, SystemExit) and options.catch:
        pdb.post_mortem()

    raise
