# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Dict, TYPE_CHECKING
import logging

# -- third party --
# -- own --
from game.base import Game
from utils.events import EventHub
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('client.parts.Lobby')
STOP = EventHub.STOP_PROPAGATION


class Lobby(object):
    def __init__(self, core: Core):
        self.core = core
        self.games: Dict[int, Game] = {}

        core.events.server_dropped += self._server_dropped

        D = core.events.server_command
        D[wire.CurrentGames] += self._current_games
        D[wire.CurrentUsers] += self._current_users

    # ----- Reactions -----
    def _current_games(self, ev: wire.msg.CurrentGames) -> wire.msg.CurrentGames:
        self.games = ev['games']
        core = self.core
        core.events.lobby_updated.emit((self.users, self.games))
        return ev

    def _current_users(self, ev: wire.msg.CurrentUsers) -> wire.msg.CurrentUsers:
        self.users = ev['users']
        core = self.core
        core.events.lobby_updated.emit((self.users, self.games))
        return ev

    def _server_dropped(self, _: None) -> None:
        self.users = []
        self.games = []
        return None

    # ----- Public Method -----
    def create_room(self, name: str, mode: str, flags: wire.msg.CreateRoomFlags) -> None:
        core = self.core
        core.server.write(wire.msg.CreateRoom(name=name, mode=mode, flags=flags))
