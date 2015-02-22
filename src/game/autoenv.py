# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from gevent import Greenlet

# -- own --
from game.game_common import Action, EventHandler, EventHandlerGroup, Game, GameEnded, GameError  # noqa
from game.game_common import GameException, GameObject, InputTransaction, InterruptActionFlow, NPC  # noqa
from game.game_common import sync_primitive  # noqa


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
