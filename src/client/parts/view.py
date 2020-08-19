# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, List, Sequence, TYPE_CHECKING
import logging

# -- third party --
from gevent import Greenlet
from mypy_extensions import TypedDict

# -- own --
from client.base import ClientGameRunner, ForcedKill, Someone, Theone, Game
from game.base import Game, GameData, GameItem, Player
from utils.events import EventHub
from utils.misc import BatchList
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
class GameView(TypedDict):
    gid: int
    type: str
    name: str
    users: List[wire.model.User]
    presence: Dict[int, bool]
    params: Dict[str, Any]
    items: Dict[int, List[str]]
    observe: bool


class View(object):
    def __init__(self, core: Core):
        self.core = core

    def __repr__(self) -> str:
        return self.__class__.__name__

    def Game(self, g: Game) -> GameView:
        core = self.core

        return {
            'gid':      core.game.gid_of(g),
            'type':     g.__class__.__name__,
            'name':     core.game.name_of(g),
            'started':  core.room.is_started(g),
            'online':   len(core.room.online_users_of(g)),
        }
