# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
import gevent

# -- own --
from .mock import Environ, EventTap
from game.base import EventHandler


# -- code --
class GameEnded(Exception):
    pass


def wait():
    gevent.idle(-100)
    gevent.sleep(0.01)
    gevent.idle(-100)


# class TestMisc(object):
#     def testClientUiHelper(self):
#         env = Environ()
#         # t = EventTap()

#         _ = env.server_core()
#         proton = env.client_core()
#         proton.game.get_all_metadata()
