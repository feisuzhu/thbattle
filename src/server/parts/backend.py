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
        self.message = ', '.join(
            '%s: %s' % ('.'.join(e['path']), e['message'])
            for e in errors
        )

    def __repr__(self) -> str:
        return 'BackendError(%s)' % repr(self.message)


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

    def __init__(self, core: Core):
        self.core = core

    def __repr__(self) -> str:
        return self.__class__.__name__

    def query(self, q: str, **vars: Mapping[str, Any]) -> Dict[str, Any]:
        q = self._strip(q)
        if q not in self.MOCKED:
            raise Exception("Can't mock query %s" % q)

        return self.MOCKED[q](vars)

    def _strip(self, q: str) -> str:
        q = q.strip()
        q = re.sub(r'[\r\n]', q, '')
        q = re.sub(r' +', q, ' ')
        return q

    def _reg(f: Callable, strip: Any = _strip, MOCKED: Any = MOCKED) -> Callable:  # type: ignore
        q = strip(None, f.__doc__)
        MOCKED[q] = f
        return f

    @_reg
    def gameId(self) -> Any:
        '''
        query { gameId }
        '''
        return {'gameId': random.randint(0, 1000000)}
