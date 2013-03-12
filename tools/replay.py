
#!/usr/bbin/python2
# -*- coding: utf-8 -*-

import sys
sys.path.append('../src')

from game import autoenv
autoenv.init('Client')

from game.autoenv import Game
from client.core import PeerPlayer, TheLittleBrother, PlayerList

from account.freeplay import Account

import re
RE_GAMEDATA = re.compile('^INFO:Server:GAME_READ: (.*)$', re.MULTILINE)

import simplejson as json

import logging
logging.basicConfig(stream=sys.stdout)
logging.getLogger().setLevel(logging.DEBUG)
log = logging.getLogger('Replay')


from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('mode', type=str)
parser.add_argument('loc', type=int)
parser.add_argument('replay_file', type=str)

options = parser.parse_args()


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
            sys.exit(0)

        for i, d in enumerate(self.gdlist):
            if d[0] == tag:
                log.info('GAME_READ: %s', repr(d))
                del self.gdlist[i]
                return d[1]
            log.info('GAME_DATA_MISS: %s', repr(d))

        log.info('GAME_DATA_MISS!!')
        sys.exit(1)

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))

    def gclear(self):
        pass


data = open(options.replay_file, 'r').read()
gdlist = RE_GAMEDATA.findall(data)
gdlist = [eval(i) for i in gdlist]
# gdlist = [json.loads(i) for i in gdlist]
server = MockServer(gdlist)
Executive = MockExecutive(server)

from client.core import game_client
game_client.Executive = Executive  # Hack

if options.mode == 'raid':
    from gamepack import THBattleRaid as GameMode
else:
    log.error('what mode?')
    sys.exit(1)

players = [PeerPlayer() for i in xrange(GameMode.n_persons)]
players[options.loc].__class__ = TheLittleBrother

g = GameMode()
g.players = PlayerList(players)
g.me = players[options.loc]
g._run()
