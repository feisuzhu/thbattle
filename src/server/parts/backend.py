# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Callable, Dict, List, TYPE_CHECKING, Mapping
import logging
import random
import re

# -- third party --
import requests

# -- own --
# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Backend')


class BackendError(Exception):
    __slots__ = ('message', 'errors')

    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        try:
            self.message = ', '.join(
                '%s: %s' % ('.'.join(e['path']), e['message'])
                for e in errors
            )
        except Exception:
            self.message = repr(errors)

    def __repr__(self) -> str:
        return f'BackendError({repr(self.message)})'


class Backend(object):
    def __init__(self, core: Core):
        self.core = core
        self._client = requests.Session()

    # ----- Public Method -----
    def query_raw(self, ql: str, **vars: Dict[str, Any]) -> dict:
        cli = self._client
        core = self.core
        resp = cli.post(core.options.backend, json={'query': ql, 'variables': vars})
        rst = resp.json()
        return rst

    def query(self, ql: str, **vars: Any) -> Dict[str, Any]:
        rst = self.query_raw(ql, **vars)
        if 'errors' in rst:
            raise BackendError(rst['errors'])

        return rst['data']


class MockBackend(object):
    MOCKED: Dict[str, Callable] = {}
    NAMED = {
        'Proton':    2,
        'Alice':     3,
        'Bob':       4,
        'Cirno':     9,
        'Daiyousei': 7,
        'Reimu':     8,
        'Marisa':    11,
        'Youmu':     12,
        'Sakuya':    16,
        'Rumia':     10,
        'Utsuho':    6,
    }

    def __init__(self, core: Core):
        self.core = core
        self.items: Dict[int, Dict[str, int]] = {}

    def __repr__(self) -> str:
        return self.__class__.__name__

    def query(self, q: str, **vars: Mapping[str, Any]) -> Dict[str, Any]:
        q = self._strip(q)
        if q not in self.MOCKED:
            raise Exception("Can't mock query %s" % q)

        return self.MOCKED[q](self, vars)

    def _strip(self, q: str) -> str:
        q = q.strip()
        q = re.sub(r'\s+', ' ', q)
        return q

    def _reg(f: Callable, strip: Any = _strip, MOCKED: Any = MOCKED) -> Callable:  # type: ignore
        q = strip(None, f.__doc__)
        MOCKED[q] = f
        return f

    @_reg
    def gameId(self, v: Any) -> Any:
        '''
        mutation { GmAllocGameId }
        '''
        return {'GmAllocGameId': random.randint(0, 1000000)}

    def pid_of(self, token: str) -> int:
        return self.NAMED.get(token, abs(hash(token)) % 120943)

    @_reg
    def login(self, v: Any) -> Any:
        '''
        query($token: String!) {
            login {
                token(token: $token) {
                    userPermissions { codename }
                    groups { permissions { codename } }
                    player { id }
                }
            }
        }
        '''

        return {
            'login': {
                'token': {
                    'userPermissions': [{"codename": "perm1"}],
                    'groups': [{
                        'permissions': [{"codename": "perm2"}, {"codename": "perm3"}]
                    }, {
                        'permissions': [{"codename": "perm4"}]
                    }],
                    "player": {
                        'id': self.pid_of(v['token']),
                    }
                },
            }
        }

    @_reg
    def archive(self, v: Any) -> Any:
        '''
        mutation ArchiveRewardRank($game: GameInput!, $archive: String!) {
            GmArchive(game: $game, archive: $archive) { id }
            GmSettleRewards(game: $game) { player { id } }
            RkAdjustRanking(game: $game) { player { id } }
        }
        '''
        return {
            'archive': {'id': 0},
            'rewards': [],
            'ranking': [],
        }

    @_reg
    def if_have_item(self, v: Any) -> Any:
        '''
        query($pid: Int!, $sku: String!) {
            player(id: $id) {
                haveItem(sku: $sku)
            }
        }
        '''
        return {'player': {'haveItem': self.items[v['pid']][v['sku']] > 0}}

    @_reg
    def remove_item(self, v: Any) -> Any:
        '''
        mutation($id: Int!, $sku: String, $r: String) {
            item {
                remove(player: $id, sku: $sku, reason: $r)
            }
        }
        '''
        self.items[v['id']][v['sku']] -= 1
        return {'item': {'remove': True}}
