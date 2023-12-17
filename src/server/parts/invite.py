# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Dict, Optional, Set, TYPE_CHECKING, Tuple, TypedDict
import logging

# -- third party --
# -- own --
from server.base import Game
from server.endpoint import Client
from server.utils import command
from utils.events import EventHub, WithPriority
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Invite')


class InviteAssocOnGame(TypedDict):
    invited: Set[int]
    banned: Dict[int, Set[int]]


def A(self: Invite, g: Game) -> InviteAssocOnGame:
    return g._[self]


class Invite(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.game_created += self.handle_game_created
        core.events.game_left += self.handle_game_left

        D = core.events.client_command
        D[wire.Invite] += self._invite
        D[wire.Kick] += self._kick
        D[wire.JoinRoom] += WithPriority(self._room_join_invite_limit, -3)

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_game_created(self, g: Game) -> Game:
        assoc: InviteAssocOnGame = {
            'invited': set(),
            'banned': defaultdict(set),
        }
        g._[self] = assoc
        return g

    def handle_game_left(self, ev: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, c = ev
        core = self.core

        for bl in A(self, g)['banned'].values():
            bl.discard(core.auth.pid_of(c))

        return ev

    # ----- Commands -----
    @command('*')
    def _room_join_invite_limit(self, u: Client, ev: wire.JoinRoom) -> Optional[EventHub.StopPropagation]:
        core = self.core
        g = core.room.get(ev.gid)
        if not g:
            return None

        flags = core.room.flags_of(g)
        pid = core.auth.pid_of(u)

        banned = A(self, g)['banned']
        invited = A(self, g)['invited']

        # banned
        if len(banned[pid]) >= max(g.n_persons // 2, 1):
            u.write(wire.Error('banned'))
            return EventHub.STOP_PROPAGATION

        # invite
        if flags.invite and pid not in invited:
            u.write(wire.Error('not_invited'))
            return EventHub.STOP_PROPAGATION

        return None

    @command('room', 'ready')
    def _invite(self, u: Client, ev: wire.Invite) -> None:
        core = self.core
        opid = ev.pid

        other = core.lobby.get(opid)
        if not (other and core.lobby.state_of(other) in ('lobby', 'ob')):
            return

        g = core.game.current(u)
        assert g

        A(self, g)['invited'].add(opid)

        other.write(wire.InviteRequest(
            pid=core.auth.pid_of(u),
            gid=core.room.gid_of(g),
            type=g.__class__.__name__,
        ))

    @command('room', 'ready')
    def _kick(self, u: Client, ev: wire.Kick) -> None:
        core = self.core
        opid = ev.pid
        other = core.lobby.get(opid)
        if not other:
            return

        g = core.game.current(u)
        g2 = core.game.current(other)
        assert g
        assert g2

        if g is not g2:
            return

        if core.lobby.state_of(other) not in ('room', 'ready'):
            return

        bl = A(self, g)['banned'][opid]
        bl.add(core.auth.pid_of(u))

        for u in core.room.online_users_of(g):
            u.write(wire.KickRequest(
                pid=core.auth.pid_of(u),
                victim=core.auth.pid_of(other),
                votes=len(bl),
            ))

        if len(bl) >= len(core.room.users_of(g)) // 2:
            A(self, g)['invited'].discard(opid)
            core.room.exit_game(other)

    # ----- Methods -----
    def add_invited(self, g: Game, u: Client) -> None:
        core = self.core
        A(self, g)['invited'].add(core.auth.pid_of(u))
