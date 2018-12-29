# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Dict, Optional, Sequence, TYPE_CHECKING, Tuple
import logging

# -- third party --
import gevent

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
        core.events.game_ended += self.handle_game_ended

        self.users: Dict[int, Client] = {}          # all users
        self.dropped_users: Dict[int, Client] = {}  # passively dropped users

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        c, f, t = ev

        if (f, t) == ('connected', 'authed'):
            self._user_join(c)

        if t == 'dropped':
            if f != 'connected':
                self._user_leave(c)

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
                    'ob',
                    'dropped',
                ],
                'initial',
                FSM.to_evhub(core.events.user_state_transition),
            )
        }
        c._[self]['state'].transit('connected')
        return c

    def handle_game_ended(self, g: Game) -> Game:
        core = self.core
        users = core.room.users_of(g)

        for u in users:
            self.dropped_users.pop(core.auth.uid_of(u), 0)

        return g

    # ----- Client Commands -----
    # ----- Public Methods -----
    def state_of(self, u: Client) -> FSM:
        return u._[self]['state']

    def all_users(self) -> BatchList[Client]:
        return BatchList(self.users.values())

    def get(self, uid: int) -> Optional[Client]:
        return self.users.get(uid)

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
        uid = core.auth.uid_of(u)
        name = core.auth.name_of(u)

        old = None

        if uid in self.users:
            # squeeze the original one out
            log.info('%s[%s] has been squeezed out' % (name, uid))
            old = self.users[uid]

        if uid in self.dropped_users:
            log.info('%s[%s] rejoining dropped game' % (name, uid))
            old = self.dropped_users.pop(uid)

            # XXX
            '''
            @gevent.spawn
            def reconnect():
                self.send_account_info(user)
            '''

        if old:
            u.pivot_to(old)
            core.events.client_pivot.emit(old)
        else:
            self.users[uid] = u
            self.state_of(u).transit('lobby')

        log.info('User %s joined, online user %d' % (name, len(self.users)))

    def _user_leave(self, u: Client) -> None:
        core = self.core
        uid = core.auth.uid_of(u)
        name = core.auth.name_of(u)
        self.users.pop(uid, 0)
        log.info('User %s left, online user %d' % (name, len(self.users)))

    @throttle(3)
    def _notify_online_users(self, ul: Sequence[Client]) -> None:
        core = self.core
        lst = [core.view.User(u) for u in self.users.values()]
        d = Endpoint.encode_bulk([wire.CurrentUsers(users=lst)])

        @gevent.spawn
        def do_send() -> None:
            for u in ul:
                u.raw_write(d)
