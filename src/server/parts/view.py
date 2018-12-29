# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING
import logging

# -- third party --
# -- own --
from server.base import Game as ServerGame
from server.endpoint import Client
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('server.parts.view')


class View(object):
    def __init__(self, core: Core):
        self.core = core

    def __repr__(self) -> str:
        return self.__class__.__name__

    def User(self, u: Client) -> wire.model.User:
        core = self.core

        return {
            'uid': core.auth.uid_of(u),
            'state': core.lobby.state_of(u).state,
        }

    def Game(self, g: ServerGame) -> wire.model.Game:
        core = self.core

        return {
            'gid':      core.room.gid_of(g),
            'type':     g.__class__.__name__,
            'name':     core.room.name_of(g),
            'started':  core.room.is_started(g),
            'online':   len(core.room.online_users_of(g)),
        }

    def GameDetail(self, g: ServerGame) -> wire.model.GameDetail:
        core = self.core

        return {
            # HACK: workaround TypedDict limitations
            'gid':      core.room.gid_of(g),
            'type':     g.__class__.__name__,
            'name':     core.room.name_of(g),
            'started':  core.room.is_started(g),
            'online':   len(core.room.online_users_of(g)),
            # **self.Game(g),
            'users':  [self.User(u) for u in core.room.users_of(g)],
            'params': core.game.params_of(g),
            'items':  core.item.item_skus_of(g),
        }
