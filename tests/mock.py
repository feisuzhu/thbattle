# -*- coding: utf-8 -*-

# -- stdlib --
from collections import deque
from typing import Callable, Dict
import logging
import random
import re

# -- third party --
from gevent.event import Event
from gevent.queue import Queue
import gevent

# -- own --
from endpoint import Endpoint, EndpointDied
from server.base import Player
from server.core import Core
from server.endpoint import Client
from utils.misc import hook
from server.parts.backend import MockBackend
from server.endpoint import MockClient


# -- code --
log = logging.getLogger('mock')


class ServerWorld(object):
    def __init__(self):
        self.core = core = Core(disables=[
            'archive', 'connect', 'stats', 'backend'
        ])
        core.backend = MockBackend(core)

    def client(self):
        core = self.core
        cli = MockClient(core)
        cli.connected()
        return cli

    def fullgame(self, cls=None, flags={}):
        if not cls:
            from thb.thb2v2 import THBattle2v2 as cls

        base = random.randint(1, 1000000)
        core = self.core
        g = core.room.create_game(cls, 'Game-%s' % base, flags)
        core.game.halt_on_start(g)

        for i in range(g.n_persons):
            u = self.client()
            assert core.lobby.state_of(u) == 'connected'
            core.auth.set_auth(u, base + i, 'UID%d' % (base + i))
            core.lobby.state_of(u).transit('authed')
            core.room.join_game(g, u, i)
            core.room.get_ready(u)

        core.game.get_bootstrap_action(g)

        return g

    def start_game(self, g):
        core = self.core
        for u in core.room.users_of(g):
            s = core.lobby.state_of(u)
            s == 'room' and s.transit('ready')

        gevent.sleep(0.01)


def hook_game(g):
    @hook(g)
    def pause(*a):
        pass

    g.synctag = 0
