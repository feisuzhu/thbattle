# -*- coding: utf-8 -*-

# -- stdlib --
from abc import ABCMeta
from typing import Any, Optional, Sequence

# -- third party --
# -- own --
from game.base import Game as BaseGame, InputTransaction, Inputlet


# -- code --
def user_input(
    players: Sequence[Any],
    inputlet: Inputlet,
    timeout: int=25,
    type: str='single',
    trans: Optional[InputTransaction]=None,
):
    ...

Game = BaseGame


def init(place: str):
    ...
