# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING
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

        D = core.events.server_command
        D[wire.CurrentUsers] += self._current_users
        D[wire.LobbyStatus] += self._lobby_status

    # ----- Reactions -----
    def _current_users(self, ev: wire.msg.CurrentUsers) -> wire.msg.CurrentUsers:
        core = self.core
        core.events.lobby_users.emit(ev.users)
        return ev

    def _lobby_status(self, ev: wire.msg.LobbyStatus) -> wire.msg.LobbyStatus:
        core = self.core
        core.events.lobby_status.emit(ev)
        return ev
