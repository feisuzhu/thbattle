# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Sequence, Set, TYPE_CHECKING, Tuple, TypedDict
import logging

# -- third party --
# -- own --
from server.endpoint import Client
from server.utils import command
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Auth')


class AuthAssocOnClient(TypedDict):
    pid: int
    kedama: bool
    permissions: Set[str]


def A(self: Auth, v: Client) -> AuthAssocOnClient:
    return v._[self]


class Auth(object):
    def __init__(self, core: Core):
        self.core = core
        self._kedama_pid = 10032
        self._allow_kedama = True

        core.events.user_state_transition += self.handle_user_state_transition
        D = core.events.client_command
        D[wire.Auth] += self._auth

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        u, f, t = ev

        if (f, t) == ('initial', 'connected'):
            from settings import VERSION
            core = self.core
            u.write(wire.Greeting(node=core.options.node, version=VERSION))
            assoc: AuthAssocOnClient = {
                'pid': 0,
                'kedama': False,
                'permissions': set(),
            }
            u._[self] = assoc

        return ev

    # ----- Command -----

    @command('connected')
    def _auth(self, u: Client, m: wire.Auth) -> None:
        core = self.core
        token = m.token
        assoc: AuthAssocOnClient

        from server.parts.backend import BackendError

        if token == '':
            if self._allow_kedama:
                pid = -self._kedama_pid
                self._kedama_pid += 1
                u.write(wire.AuthSuccess(pid))
                assoc = {
                    'pid': pid,
                    'kedama': True,
                    'permissions': set(),
                }
                u._[self] = assoc
                core.lobby.state_of(u).transit('authed')
            else:
                u.write(wire.AuthError('not_available'))

            return

        try:
            rst = core.backend.query('''
                query($token: String) {
                    user(token: $token) {
                        isActive
                        userPermissions {
                            codename
                        }
                        groups {
                            permissions {
                                codename
                            }
                        }
                        player {
                            id
                        }
                    }
                }
            ''', token=token)
        except BackendError:
            log.exception("Error getting user by token")
            u.write(wire.AuthError('not_available'))
            return

        if not rst or not rst['user']:
            u.write(wire.AuthError('invalid_credentials'))
            return

        rst = rst['user']

        if not rst['isActive']:
            u.write(wire.AuthError('not_available'))
        else:
            pid = int(rst['player']['id'])
            u.write(wire.AuthSuccess(pid))
            assoc = {
                'pid': pid,
                'kedama': False,
                'permissions': set(
                    [i['codename'] for i in rst['userPermissions']] +
                    [i['codename'] for i in rst['groups']['permissions']]
                ),
            }
            u._[self] = assoc
            core.lobby.state_of(u).transit('authed')

    # ----- Public Methods -----
    def allow_kedama(self) -> None:
        self._allow_kedama = True

    def deny_kedama(self) -> None:
        self._allow_kedama = False

    def pid_of(self, u: Client) -> int:
        return A(self, u)['pid']

    def is_kedama(self, u: Client) -> bool:
        return A(self, u)['kedama']

    def set_auth(self, u: Client, pid: int = 1, kedama: bool = False, permissions: Sequence[str] = []) -> None:
        assoc: AuthAssocOnClient = {
            'pid': pid,
            'kedama': kedama,
            'permissions': set(permissions),
        }
        u._[self] = assoc
