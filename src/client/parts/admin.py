# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING

# -- third party --
# -- own --
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
class Admin(object):
    def __init__(self, core: Core):
        self.core = core

    # ----- Public Methods -----
    def kick(self, uid: int) -> None:
        core = self.core
        core.server.write(wire.msg.AdminKick(uid=uid))

    def clearzombies(self) -> None:
        core = self.core
        core.server.write(wire.msg.AdminClearZombies())

    def migrate(self) -> None:
        core = self.core
        core.server.write(wire.msg.AdminMigrate())

    def stacktrace(self) -> None:
        core = self.core
        core.server.write(wire.msg.AdminStacktrace())

    def kill_game(self, gid: int) -> None:
        core = self.core
        core.server.write(wire.msg.AdminKillGame(gid=gid))
