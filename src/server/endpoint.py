# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import List, Optional, Sequence, TYPE_CHECKING, cast
import logging

# -- third party --
from gevent import Greenlet, getcurrent

# -- own --
from endpoint import Endpoint, EndpointDied
from utils.misc import MockMeta
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
                continue

            except Exception as e:
                if core.options.paranoid:
                    core.crash(e)
                    raise
                log.exception("Error occurred when handling client command")

        core.events.client_dropped.emit(self)

    def serve(self) -> None:
        self._before_serve()
        self._serve()

    def close(self) -> None:
        self._ep and self._ep.close()
        self._ep = None
        self._gr and self._gr.kill(EndpointDied)
        self._gr = None

    def is_dead(self) -> bool:
        return not self._gr or self._gr.ready()

    def pivot_to(self, other: Client) -> None:
        if not self._ep:
            raise Exception("self._ep is not valid!")

        other._ep = self._ep
        self._ep = None
        self._gr and self._gr.kill()  # this skips client_dropped event

        core = self.core
        if other._ep:
            other._gr and other._gr.kill(Pivot)
        else:
            other._gr = core.runner.spawn(other._serve)

    def __repr__(self) -> str:
        if self._ep:
            return '%s:%s:%s' % (
                self.__class__.__name__,
                *self._ep.address,
            )
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


class MockClient(Client, metaclass=MockMeta):

    def __init__(self, core: Core):
        self.core = core
        self.dead = False
        self.written_messages: List[wire.ServerToClient] = []

        self._: dict = {}

    def dropped(self) -> None:
        core = self.core
        core.events.client_dropped.emit(self)

    def connected(self) -> None:
        core = self.core
        core.events.client_connected.emit(self)

    def recv(self, v: wire.ServerToClient) -> None:
        self.written_messages.append(v)

    def close(self) -> None:
        pass

    def is_dead(self) -> bool:
        return self.dead

    def pivot_to(self, other: Client) -> None:
        pass

    def __repr__(self) -> str:
        return '%s:%s:%s' % (
            self.__class__.__name__,
            'FIXME', 'FIXME'
        )

    def write(self, v: wire.ServerToClient) -> None:
        self.written_messages.append(v)

    def write_bulk(self, vl: Sequence[wire.ServerToClient]) -> None:
        self.written_messages.extend(vl)

    def raw_write(self, v: bytes) -> None:
        self.written_messages.extend(cast(List[wire.ServerToClient], Endpoint.decode_bytes(v)))
