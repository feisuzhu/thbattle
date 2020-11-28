# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import List, TYPE_CHECKING
import logging

# -- third party --
# -- own --
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
        self.games: List[wire.model.Game] = []
        self.users: List[wire.model.User] = []

        core.events.server_dropped += self._server_dropped

        D = core.events.server_command
        D[wire.CurrentGames] += self._current_games
        D[wire.CurrentUsers] += self._current_users

    # ----- Reactions -----
    def _current_games(self, ev: wire.msg.CurrentGames) -> wire.msg.CurrentGames:
        core = self.core
        self.games = ev.games
        core.events.lobby_games.emit(ev.games)
        return ev

    def _current_users(self, ev: wire.msg.CurrentUsers) -> wire.msg.CurrentUsers:
        core = self.core
        self.users = ev.users
        core.events.lobby_users.emit(ev.users)
        return ev

    def _server_dropped(self, v: bool) -> bool:
        self.users = []
        self.games = []
        return v
