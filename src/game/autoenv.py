# -*- coding: utf-8 -*-
from game_common import GameError, GameEnded, sync_primitive, InterruptActionFlow, GameException, GameObject, Action, EventHandler, InputTransaction, Game  # noqa
from gevent import Greenlet


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
