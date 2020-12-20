# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Optional, Sequence, TYPE_CHECKING, cast, Type
import logging

# -- third party --
from gevent import Greenlet, getcurrent

# -- own --
from endpoint import Endpoint, EndpointDied
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('server.core.endpoint')


class Pivot(Exception):
    pass


class Client(object):
    __slots__ = ('_ep', '_gr', 'core', '_')

    def __init__(self, core: Core, ep: Optional[Endpoint]):
        self._ep: Optional[Endpoint] = ep
        self._gr: Optional[Greenlet] = None
        self.core = core

        self._: dict = {}

    def _before_serve(self) -> None:
        core = self.core
        self._gr = getcurrent()
        core.events.client_connected.emit(self)

    def _serve(self) -> None:
        core = self.core
        tbl = core.events.client_command

        while True:
            if not self._ep:
                break

            try:
                for msg in self._ep.messages(timeout=90):
                    tbl[msg.__class__].emit((self, msg))

            except EndpointDied:
                break

            except Pivot:
                return

            except Exception as e:
                if core.options.testing:
                    core.crash(e)
                    raise
                log.exception("Error occurred when handling client command")
            finally:
                self._ep and self._ep.close()
                self._ep = None
                self._gr = None

        core.events.client_dropped.emit(self)

    def serve(self) -> None:
        self._before_serve()
        self._serve()

    def terminate(self, exc: Type[Exception] = EndpointDied) -> None:
        self._gr and self._gr.kill(exc)

    def is_dead(self) -> bool:
        return not self._gr or self._gr.ready()

    def pivot_to(self, new: Client) -> None:
        core = self.core

        cur = getcurrent()
        new._ = dict(self._)

        assert cur is not self._gr
        self.terminate(Pivot)

        if not new._gr:
            new._gr = core.runner.spawn(new._serve)

    def __repr__(self) -> str:
        if self._ep:
            return '%s:%s:%s' % (
                self.__class__.__name__,
                *self._ep.address,
            )  # noqa
        else:
            return '%s:?' % (
                self.__class__.__name__,
            )

    def get_greenlet(self) -> Optional[Greenlet]:
        return self._gr

    def write(self, v: wire.ServerToClient) -> None:
        ep = self._ep
        if ep: ep.write(v)

    def write_bulk(self, vl: Sequence[wire.ServerToClient]) -> None:
        ep = self._ep
        if ep: ep.write_bulk(cast(Sequence[wire.Message], vl))

    def raw_write(self, v: bytes) -> None:
        ep = self._ep
        if ep: ep.raw_write(v)
