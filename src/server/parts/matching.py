# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Dict, List, Set, TYPE_CHECKING, Tuple, TypedDict
import logging
import time

# -- third party --
# -- own --
from endpoint import Endpoint
from game.base import Game
from server.endpoint import Client
from server.utils import command
from utils.misc import throttle
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Matching')


class MatchingAssocOnClient(TypedDict):
    modes: List[str]


def Au(self: Matching, u: Client) -> MatchingAssocOnClient:
    return u._[self]


class MatchingAssocOnGame(TypedDict):
    match_time: float
    fallen: bool
    tearing_down: bool


def Ag(self: Matching, g: Game) -> MatchingAssocOnGame:
    return g._[self]


class Matching(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.user_state_transition += self.handle_user_state_transition
        core.events.core_initialized += self.handle_core_initialized
        core.events.client_dropped += self.handle_client_dropped
        core.events.game_left += self.handle_game_left

        core.tasks['matching/gc-stuck-matching'] = self._task_gc_stuck_matching

        D = core.events.client_command
        D[wire.StartMatching] += self._start_matching
        D[wire.QueryMatching] += self._query_matching

        self.outstanding: Dict[str, Set[Client]] = {}
        self.pending_start: List[Game] = []

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_core_initialized(self, ev: Core) -> Core:
        from thb import modes
        order = list(modes)
        order.sort(key=lambda v: modes[v].n_persons, reverse=True)

        for m in order:
            self.outstanding[m] = set()

        return ev

    def handle_client_dropped(self, c: Client) -> Client:
        self._clear(c)
        return c

    def handle_game_left(self, v: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, u = v
        if g in self.pending_start:
            Ag(self, g)['fallen'] = True

        return v

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        c, f, t = ev

        if t in ('room', 'ready', 'game'):
            self._clear(c)

        elif t == 'lobby':
            c.write(wire.StartMatching(modes=Au(self, c)['modes']))

        elif t == 'connected':
            assoc: MatchingAssocOnClient = {
                'modes': [],
            }
            c._[self] = assoc

        if t != 'freeslot':
            self.notify_matching_for_all()

        return ev

    def _notify_matching(self, ul: List[Client]) -> None:
        core = self.core

        matches = {
            k: sorted([core.auth.pid_of(u) for u in v])
            for k, v in self.outstanding.items()
        }

        d = Endpoint.encode_bulk([wire.CurrentMatching(matches=matches)])

        @core.runner.spawn
        def do_send() -> None:
            for u in ul:
                u.raw_write(d)

    def _task_gc_stuck_matching(self) -> None:
        core = self.core
        while True:
            core.runner.sleep(1)
            self._do_gc_stuck_matching()

    def _do_gc_stuck_matching(self) -> None:
        nxt: List[Game]
        core = self.core
        last = self.pending_start
        self.pending_start = nxt = []
        for g in last:
            if core.room.is_started(g):
                continue

            if Ag(self, g)['tearing_down']:
                continue

            if Ag(self, g)['fallen']:
                self._teardown(g)
                continue

            if Ag(self, g)['match_time'] + 15 < time.time():
                self._teardown(g)
                continue

            nxt.append(g)

    def _teardown(self, g: Game) -> None:
        if Ag(self, g)['tearing_down']:
            return

        Ag(self, g)['tearing_down'] = True
        core = self.core

        for u in core.room.online_users_of(g):
            core.room.exit_game(u)

    @throttle(0.5)
    def notify_matching_for_all(self) -> None:
        core = self.core
        self._notify_matching(core.lobby.all_users())

    # ----- Public Methods -----
    def do_match(self) -> None:
        core = self.core
        from thb import modes

        while True:
            for m in self.outstanding:
                candidates = []
                avail = self.outstanding[m]
                cls = modes[m]
                if len(avail) < cls.n_persons:
                    continue

                for _ in range(cls.n_persons):
                    u = avail.pop()
                    assert core.lobby.state_of(u) == 'lobby'
                    candidates.append(u)

                for u in candidates:
                    self._clear(u)

                g = core.room.create_game(cls, "匹配的游戏", core.room.RoomFlags(matching=True))
                ag: MatchingAssocOnGame = {
                    'match_time': time.time(),
                    'fallen': False,
                    'tearing_down': False,
                }
                g._[self] = ag
                for u in candidates:
                    core.room.join_game(g, u)

                self.pending_start.append(g)

                break
            else:
                return

    # ----- Methods -----
    def _clear(self, u: Client) -> None:
        Au(self, u)['modes'] = []
        for m, s in self.outstanding.items():
            s.discard(u)

    # ----- Client Commands -----
    @command('lobby')
    def _start_matching(self, u: Client, ev: wire.StartMatching) -> None:
        from thb import modes

        self._clear(u)
        filtered = list(set(modes) & set(ev.modes))
        Au(self, u)['modes'] = filtered
        u.write(wire.StartMatching(modes=filtered))

        for m in filtered:
            self.outstanding[m].add(u)

        self.do_match()
        self.notify_matching_for_all()

    @command('lobby')
    def _query_matching(self, u: Client, ev: wire.QueryMatching) -> None:
        self._notify_matching([u])
