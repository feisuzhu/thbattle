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
log = logging.getLogger('client.parts.Observe')
STOP = EventHub.STOP_PROPAGATION


class Observe(object):
    def __init__(self, core: Core):
        self.core = core

        D = core.events.server_command
        D[wire.ObserverEnter] += self._observer_enter
        D[wire.ObserverLeave] += self._observer_leave
        D[wire.ObserveRequest] += self._observe_request

    # ---- Reactions -----
    def _observer_enter(self, ev: wire.ObserverEnter) -> wire.ObserverEnter:
        core = self.core
        core.events.observer_enter.emit((ev.observer, ev.observee))
        return ev

    def _observer_leave(self, ev: wire.ObserverLeave) -> wire.ObserverLeave:
        core = self.core
        core.events.observer_leave.emit((ev.observer, ev.observee))
        return ev

    def _observe_request(self, ev: wire.ObserveRequest) -> wire.ObserveRequest:
        core = self.core
        core.events.observe_request.emit(ev.uid)
        return ev

    # ----- Public Method -----
    def observe(self, uid: int) -> None:
        core = self.core
        core.server.write(wire.Observe(uid=uid))

    def grant(self, uid: int, grant: bool) -> None:
        core = self.core
        core.server.write(wire.GrantObserve(uid=uid, grant=grant))

    def kick(self, uid: int) -> None:
        core = self.core
        core.server.write(wire.KickObserver(uid=uid))
