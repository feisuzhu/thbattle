# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Dict, List, Set, TYPE_CHECKING, Tuple, TypedDict
import logging

# -- third party --
# -- own --
from server.endpoint import Client
from server.utils import command
from utils.misc import LoopBreaker
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


class Matching(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.user_state_transition += self.handle_user_state_transition
        core.events.core_initialized += self.handle_core_initialized
        core.events.client_dropped += self.handle_client_dropped

        D = core.events.client_command
        D[wire.StartMatching] += self._start_matching

        self.outstanding: Dict[str, Set[Client]] = {}

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

        return ev

    # ----- Public Methods -----
    def do_match(self) -> None:
        core = self.core
        from thb import modes

        for loop in LoopBreaker(False):
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

                g = core.room.create_game(cls, "匹配的游戏", {})
                for u in candidates:
                    core.room.join_game(g, u)

                loop.cont()
                break

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
        if not filtered:
            return

        for m in filtered:
            self.outstanding[m].add(u)

        self.do_match()
