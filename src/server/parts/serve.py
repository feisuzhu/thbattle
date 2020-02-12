# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, TYPE_CHECKING
import logging
import urllib.parse

# -- third party --
from gevent.server import StreamServer

# -- own --
# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Interconnect')


class Serve(object):
    def __init__(self, core: Core):
        self.core = core
        core.tasks['serve/accept'] = self.accept

    def __repr__(self) -> str:
        return self.__class__.__name__

    def accept(self) -> None:
        core = self.core
        a = urllib.parse.urlparse(core.options.listen)
        assert a.scheme == 'tcp'
        server = StreamServer((a.hostname, a.port), self._serve, None)
        server.serve_forever()

    # ----- Methods -----
    def _serve(self, sock: Any, addr: Any) -> None:
        core = self.core

        from endpoint import Endpoint
        from server.endpoint import Client

        ep = Endpoint(sock, addr)
        cli = Client(core, ep)
        cli.serve()
