# -*- coding: utf-8 -*-

import logging
log = logging.getLogger('mock')

from utils import hook
from gevent.event import Event
from network import Endpoint
import simplejson as json
import re


class MockConnection(object):
    def __init__(self, gdlist):
        self.gdlist = gdlist
        self.gdevent = Event()
        self.gdevent.clear()
        self.exhausted = False
        self.gdhistory = []

    def gexpect(self, tag, blocking=False):
        assert self.gdlist, 'GAME_DATA_EXHAUSTED!'
        # log.info('GAME_EXPECT: %s', repr(tag))

        log.info('GAME_EXPECT: %s', tag)
        glob = False
        if tag.endswith('*'):
            glob = True

        missed = False
        for i, d in enumerate(self.gdlist):
            cond = d[0] == tag
            cond = cond or glob and d[0].startswith(tag[:-1])
            cond = cond or d[0].startswith('>') and re.match(d[0][1:] + '$', tag)
            if cond:
                log.info('GAME_READ: %s', repr(d))
                del self.gdlist[i]

                if not self.gdlist:
                    log.info('Game data exhausted.')

                return d
            if not missed:
                log.info('GAME_DATA_MISS: %s', repr(d))
                missed = True

        assert False, 'GAME_DATA_MISS! EXPECTS "%s"' % tag

    def gwrite(self, tag, data):
        log.debug('GAME_WRITE: %s', repr([tag, data]))
        encoded = Endpoint.encode(data)
        self.gdhistory.append([tag, json.loads(encoded)])


    def gclear(self):
        assert self.exhausted


def create_mock_player(gdlist):
    conn = MockConnection(gdlist[:])
    from server.core import Player
    return Player(conn)


def hook_game(g):
    @hook(g)
    def pause(*a):
        pass

    g.synctag = 0

    from client.core import Game
    Game.getgame = staticmethod(lambda: g)

    from server.core import Game
    Game.getgame = staticmethod(lambda: g)

    g.__class__.getgame = staticmethod(lambda: g)
