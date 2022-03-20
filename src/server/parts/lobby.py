# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Dict, Optional, Sequence, TYPE_CHECKING, Tuple
import logging

# -- third party --
# -- own --
from endpoint import Endpoint
from server.base import Game
from server.endpoint import Client
from utils.events import FSM
from utils.misc import BatchList, throttle
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Lobby')


class Lobby(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.client_connected += self.handle_client_connected
        core.events.user_state_transition += self.handle_user_state_transition
        core.events.game_ended += self.handle_game_ended_aborted
        core.events.game_aborted += self.handle_game_ended_aborted
        core.events.client_dropped += self.handle_client_dropped

        self.users: Dict[int, Client] = {}          # all players
        self.dropped_users: Dict[int, Client] = {}  # passively dropped players

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        c, f, t = ev

        if (f, t) == ('uninitialized', 'freeslot'):
            # Just don't bother, core is not running at this time
            return ev

        if (f, t) == ('connected', 'authed'):
            self._user_join(c)

        ul = [u for u in self.users.values() if u._[self]['state'] == 'lobby']
        self._notify_online_users(ul)

        return ev

    def handle_client_connected(self, c: Client) -> Client:
        core = self.core
        c._[self] = {
            'state': FSM(
                c,
                [
                    'initial',
                    'connected',
                    'authed',
                    'lobby',
                    'room',
                    'ready',
                    'game',
                    'finishing',
                    'ob',
                    'leaving',
                ],
                'initial',
                FSM.to_evhub(core.events.user_state_transition),
            )
        }
        c._[self]['state'].transit('connected')
        return c

    def handle_client_dropped(self, c: Client) -> Client:
        if c._[self]['state'] != 'connected':
            self._user_leave(c)

        return c

    def handle_game_ended_aborted(self, g: Game) -> Game:
        core = self.core
        users = core.room.users_of(g)

        for u in users:
            self.dropped_users.pop(core.auth.pid_of(u), 0)

        return g

    # ----- Client Commands -----
    # ----- Public Methods -----
    def state_of(self, u: Client) -> FSM:
        return u._[self]['state']

    def all_users(self) -> BatchList[Client]:
        return BatchList(self.users.values())

    def get(self, pid: int) -> Optional[Client]:
        return self.users.get(pid)

    def init_freeslot(self, c: Client) -> None:
        core = self.core
        c._[self] = {
            'state': FSM(
                c, ['uninitialized', 'freeslot'], 'uninitialized',
                FSM.to_evhub(core.events.user_state_transition),
            )
        }

    # ----- Methods -----
    def _user_join(self, u: Client) -> None:
        core = self.core
        pid = core.auth.pid_of(u)

        old = None

        if pid in self.users:
            # squeeze the original one out
            log.info('PID:%s has been squeezed out', pid)
            old = self.users[pid]

        if pid in self.dropped_users:
            log.info('PID:%s rejoining dropped game', pid)
            old = self.dropped_users.pop(pid)

        if old is not None:
            old.pivot_to(u)
            self.users[pid] = u
            core.events.client_pivot.emit(u)
        else:
            self.users[pid] = u
            self.state_of(u).transit('lobby')

        log.info('User PID:%s joined, online user %d', pid, len(self.users))

    def _user_leave(self, u: Client) -> None:
        core = self.core
        u._[self]['state'].transit('leaving')
        pid = core.auth.pid_of(u)
        self.users.pop(pid, 0)
        log.info('User PID:%s left, online user %d', pid, len(self.users))

    @throttle(3)
    def _notify_online_users(self, ul: Sequence[Client]) -> None:
        core = self.core
        lst = [core.view.User(u) for u in self.users.values()]
        d = Endpoint.encode_bulk([wire.CurrentUsers(users=lst)])

        @core.runner.spawn
        def do_send() -> None:
            for u in ul:
                u.raw_write(d)
