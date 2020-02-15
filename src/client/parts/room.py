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
log = logging.getLogger('client.parts.Room')
STOP = EventHub.STOP_PROPAGATION


class Room(object):
    def __init__(self, core: Core):
        self.core = core

        D = core.events.server_command
        D[wire.ObserverEnter] += self._observer_enter
        D[wire.ObserverLeave] += self._observer_leave

    # ---- Reactions -----
    def _observer_enter(self, ev: wire.ObserverEnter) -> wire.ObserverEnter:
        core = self.core
        core.events.observer_enter.emit(ev)
        return ev

    def _observer_leave(self, ev: wire.ObserverLeave) -> wire.ObserverLeave:
        core = self.core
        core.events.observer_leave.emit(ev)
        return ev

    # ----- Public Method -----
    def create(self, name: str, mode: str, flags: wire.CreateRoomFlags) -> None:
        core = self.core
        core.server.write(wire.CreateRoom(name=name, mode=mode, flags=flags))

    def join(self, gid: int, slot: int = None) -> None:
        core = self.core
        core.server.write(wire.JoinRoom(gid=gid, slot=slot))

    def leave(self):
        core = self.core
        core.server.write(wire.LeaveRoom())

    def get_ready(self):
        core = self.core
        core.server.write(wire.GetReady())

    def cancel_ready(self):
        core = self.core
        core.server.write(wire.CancelReady())

    def change_location(self, loc: int):
        core = self.core
        core.server.write(wire.ChangeLocation(loc=loc))

    def observe(self, uid: int):
        core = self.core
        core.server.write(wire.Observe(uid=uid))

    def grant_observe(self, uid: int, grant: bool):
        core = self.core
        core.server.write(wire.GrantObserve(uid=uid, grant=grant))

    def kick_observer(self, uid: int):
        core = self.core
        core.server.write(wire.KickObserver(uid=uid))
