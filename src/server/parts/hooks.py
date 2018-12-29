# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, List, TYPE_CHECKING
import logging

# -- third party --
# -- own --
from game.base import EventHandler
from server.base import Game


# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401

# -- code --
log = logging.getLogger('server.parts.hooks')


class ServerEventHooks(EventHandler):
    def __init__(self) -> None:
        self.hooks: List[EventHandler] = [
        ]

    def handle(self, evt_type: str, arg: Any) -> Any:
        for h in self.hooks:
            arg = h.handle(evt_type, arg)

        return arg


class Hooks(object):
    def __init__(self, core: Core):
        self.core = core
        core.events.game_started += self.handle_game_started

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_game_started(self, g: Game) -> Game:
        g.event_observer = ServerEventHooks()
        return g
