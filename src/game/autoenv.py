# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable

# -- third party --
# -- own --
from game.base import Game as BaseGame


# -- code --
class Game(BaseGame):
    pass


U: Callable


def user_input(*a, **k):
    return U(*a, **k)


def init(place: str):
    global U

    if place == 'Server':
        from server.base import Game as ServerGame, user_input as svr_user_input
        Game.__bases__ = (ServerGame,)
        U = svr_user_input
    elif place == 'Client':
        from client.base import Game as ClientGame, user_input as cli_user_input
        Game.__bases__ = (ClientGame,)
        U = cli_user_input
    else:
        raise Exception('Where am I?')
