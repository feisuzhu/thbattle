# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING

# -- third party --
# -- own --
from utils.events import EventHub
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
class Auth(object):
    def __init__(self, core: Core):
        self.core = core
        self.uid = 0

        D = core.events.server_command
        D[wire.AuthSuccess] += self._auth_success
        D[wire.AuthError] += self._auth_error

    def _auth_success(self, ev: wire.AuthSuccess) -> EventHub.StopPropagation:
        core = self.core
        self.uid = ev.uid
        core.events.auth_success.emit(ev.uid)
        return EventHub.STOP_PROPAGATION

    def _auth_error(self, ev: wire.AuthError) -> EventHub.StopPropagation:
        core = self.core
        core.events.auth_error.emit(ev.reason)
        return EventHub.STOP_PROPAGATION

    # ----- Public Methods -----
    def login(self, token: str) -> None:
        core = self.core
        core.server.write(wire.Auth(token))
