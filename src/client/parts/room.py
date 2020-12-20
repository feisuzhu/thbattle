# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING, Any, Optional
import logging

# -- third party --
# -- own --
from utils.events import EventHub
from game.base import Game
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
        self.current_game: Optional[Game] = None

        core.events.game_joined += self.on_game_joined
        core.events.game_left   += self.on_game_left

    # ---- Reactions -----
    def on_game_joined(self, g: Game) -> Game:
        self.current_game = g
        return g

    def on_game_left(self, g: Game) -> Game:
        self.current_game = None
        return g

    # ----- Public Method -----
    def create(self, name: str, mode: str, flags: wire.CreateRoomFlags) -> None:
        core = self.core
        core.server.write(wire.CreateRoom(name=name, mode=mode, flags=flags))

    def join(self, gid: int, slot: int = None) -> None:
        core = self.core
        core.server.write(wire.JoinRoom(gid=gid, slot=slot))

    def leave(self) -> None:
        core = self.core
        core.server.write(wire.LeaveRoom())

    def get_ready(self) -> None:
        core = self.core
        core.server.write(wire.GetReady())

    def cancel_ready(self) -> None:
        core = self.core
        core.server.write(wire.CancelReady())

    def change_location(self, loc: int) -> None:
        core = self.core
        core.server.write(wire.ChangeLocation(loc=loc))

    def get_room_users(self, gid: int = 0) -> None:
        core = self.core
        if not gid:
            if self.current_game:
                gid = core.game.gid_of(self.current_game)
            else:
                return
        core.server.write(wire.GetRoomUsers(gid=gid))

    def set_game_param(self, key: str, value: Any) -> None:
        core = self.core
        assert self.current_game
        gid = core.game.gid_of(self.current_game)
        core.server.write(wire.SetGameParam(gid=gid, pid=0, key=key, value=value))

    def use_item(self, sku: str) -> None:
        core = self.core
        core.server.write(wire.UseItem(sku=sku))

    def invite(self, pid: int) -> None:
        core = self.core
        core.server.write(wire.Invite(pid=pid))

    def kick(self, pid: int) -> None:
        core = self.core
        core.server.write(wire.Kick(pid=pid))
