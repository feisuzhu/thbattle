# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING, Optional
import logging

# -- third party --
# -- own --
from server.endpoint import Client
from server.utils import command
from utils.events import EventHub
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('server.parts.kedama')


class Kedama(object):
    def __init__(self, core: Core):
        self.core = core
        D = core.events.client_command
        D[wire.CreateRoom].subscribe(self._room_create_limit, -5)
        D[wire.JoinRoom].subscribe(self._room_join_limit, -5)
        D[wire.Invite].subscribe(self._invite_limit, -5)

    def __repr__(self) -> str:
        return self.__class__.__name__

    # ----- Commands -----
    @command()
    def _room_create_limit(self, u: Client, ev: wire.CreateRoom) -> Optional[EventHub.StopPropagation]:
        core = self.core
        from thb import modes_kedama
        if core.auth.is_kedama(u) and ev.mode not in modes_kedama:
            u.write(wire.Error('kedama_limitation'))
            return EventHub.STOP_PROPAGATION

        return None

    @command()
    def _room_join_limit(self, u: Client, ev: wire.JoinRoom) -> Optional[EventHub.StopPropagation]:
        core = self.core
        g = core.room.get(ev.gid)
        if not g:
            return None

        from thb import modes_kedama
        if core.auth.is_kedama(u) and g.__class__.__name__ not in modes_kedama:
            u.write(wire.Error('kedama_limitation'))
            return EventHub.STOP_PROPAGATION

        return None

    @command()
    def _invite_limit(self, c: Client, ev: wire.Invite) -> Optional[EventHub.StopPropagation]:
        core = self.core
        uid = core.auth.uid_of(c)
        if uid <= 0:
            c.write(wire.Error('kedama_limitation'))
            return EventHub.STOP_PROPAGATION

        return None
