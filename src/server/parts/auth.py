# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Sequence, Set, TYPE_CHECKING, Tuple
import logging

# -- third party --
from mypy_extensions import TypedDict

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
    uid: int
    name: str
    kedama: bool
    permissions: Set[str]


def A(self: Auth, v: Client) -> AuthAssocOnClient:
    return v._[self]


class Auth(object):
    def __init__(self, core: Core):
        self.core = core
        self._kedama_uid = -10032

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
                'uid': 0,
                'name': '',
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

        rst = core.backend.query('''
            query($token: String) {
                player(token: $token) {
                    id
                    user {
                        isActive
                        userPermissions {
                            codename
                        }
                        groups {
                            permissions {
                                codename
                            }
                        }
                    }
                    name
                }
            }
        ''', token=token)

        if not rst or rst['player']:
            u.write(wire.AuthError('invalid_credentials'))
            return

        rst = rst['player']

        if not rst['user']['isActive']:
            u.write(wire.AuthError('not_available'))
        else:
            uid = int(rst['id'])
            u.write(wire.AuthSuccess(uid))
            assoc: AuthAssocOnClient = {
                'uid': uid,
                'name': rst['name'],
                'kedama': False,
                'permissions': set(
                    [i['codename'] for i in rst['user']['userPermissions']] +
                    [i['codename'] for i in rst['user']['groups']['permissions']]
                ),
            }
            u._[self] = assoc
            core.lobby.state_of(u).transit('authed')

    # ----- Public Methods -----
    def uid_of(self, u: Client) -> int:
        return A(self, u)['uid']

    def name_of(self, u: Client) -> str:
        return A(self, u)['name']

    def is_kedama(self, u: Client) -> bool:
        return A(self, u)['kedama']

    def set_auth(self, u: Client, uid: int = 1, name: str = 'Foo', kedama: bool = False, permissions: Sequence[str] = []) -> None:
        assoc: AuthAssocOnClient = {
            'uid': uid,
            'name': name,
            'kedama': kedama,
            'permissions': set(permissions),
        }
        u._[self] = assoc
