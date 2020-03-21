# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING, Any
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

    # ---- Reactions -----

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

    def get_room_users(self, gid: int):
        core = self.core
        core.server.write(wire.GetRoomUsers(gid=gid))

    def set_game_param(self, gid: int, key: str, value: Any):
        core = self.core
        core.server.write(wire.SetGameParam(gid=gid, key=key, value=value))

    def invite(self, uid: int):
        core = self.core
        core.server.write(wire.Invite(uid=uid))

    def kick(self, uid: int):
        core = self.core
        core.server.write(wire.Kick(uid=uid))
