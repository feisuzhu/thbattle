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
    permissions: Set[str]


def A(self: Auth, v: Client) -> AuthAssocOnClient:
    return v._[self]


class Auth(object):
    def __init__(self, core: Core):
        self.core = core

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
            u.write(wire.AuthError('not_available'))
            return

        try:
            rst = core.backend.query('''
                query($token: String!) {
                    login {
                        token(token: $token) {
                            userPermissions { codename }
                            groups { permissions { codename } }
                            player { id }
                        }
                    }
                }
            ''', token=token)
        except BackendError:
            log.exception("Error getting user by token")
            u.write(wire.AuthError('internal_error'))
            return

        if not rst or not rst['login']['token']:
            u.write(wire.AuthError('invalid_credentials'))
            return

        rst = rst['login']['token']

        pid = int(rst['player']['id'])
        u.write(wire.AuthSuccess(pid))
        assoc = {
            'pid': pid,
            'permissions': set(
                [i['codename'] for i in rst['userPermissions']] +
                [i['codename'] for g in rst['groups'] for i in g['permissions']]
            ),
        }
        u._[self] = assoc
        core.lobby.state_of(u).transit('authed')

    # ----- Public Methods -----
    def pid_of(self, u: Client) -> int:
        return A(self, u)['pid']

    def set_auth(self, u: Client, pid: int = 1, permissions: Sequence[str] = []) -> None:
        assoc: AuthAssocOnClient = {
            'pid': pid,
            'permissions': set(permissions),
        }
        u._[self] = assoc
