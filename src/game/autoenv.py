# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from gevent import Greenlet

# -- own --
from game.base import Action, ActionShootdown, EventHandler, EventHandlerGroup, Game, GameEnded  # noqa
from game.base import GameError, GameException, GameItem, GameObject, InputTransaction  # noqa
from game.base import InterruptActionFlow, NPC, get_seed_for, list_shuffle, sync_primitive  # noqa


# -- code --
class Game(Greenlet, Game):
    pass


def user_input(*a, **k):
    return U(*a, **k)  # noqa


def init(place, custom=None):
    global Game, user_input
    if custom:
        locals.update(custom)
    elif place == 'Server':
        from server.core import Game as G, user_input as U
    elif place == 'Client':
        from client.core import Game as G, user_input as U  # noqa
    else:
        raise Exception('Where am I?')

    Game.__bases__ = (G,)
    globals().update(locals())
