# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Optional, TYPE_CHECKING, cast, List
from urllib.parse import urlparse
import logging
import socket

# -- third party --
from gevent import Greenlet
import gevent

# -- own --
from endpoint import Endpoint
from utils.events import EventHub
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('client.parts.Server')
STOP = EventHub.STOP_PROPAGATION


class Server(object):
    def __init__(self, core: Core):
        self.core = core

        self.server_name = 'Unknown'
        self.state = 'initial'

        self._ep: Optional[Endpoint] = None
        self._recv_gr: Optional[Greenlet] = None
        self._beater_gr: Optional[Greenlet] = None

        D = core.events.server_command
        D[wire.Greeting] += self._greeting
        D[wire.Ping] += self._ping

    def _greeting(self, ev: wire.Greeting) -> wire.Greeting:
        from settings import VERSION

        core = self.core

        if ev.version != VERSION:
            self.disconnect()
            core.events.version_mismatch.emit(None)
        else:
            self.server_name = ev.node
            core.events.server_connected.emit(None)

        return ev

    def _ping(self, ev: wire.Ping) -> wire.Ping:
        self.write(wire.Pong())
        return ev

    # ----- Public Methods -----
    def connect(self, uri: str) -> None:
        core = self.core

        uri = urlparse(uri)
        assert uri.scheme == 'tcp'

        if not self.state == 'initial':
            return

        try:
            self.state = 'connecting'
            addr = uri.hostname, uri.port
            s = socket.create_connection(addr)
            self._ep = Endpoint(s, addr)
            self._recv_gr = core.runner.spawn(self._recv)
            self._beater_gr = core.runner.spawn(self._beat)
            self.state = 'connected'
        except Exception:
            self.state = 'initial'
            log.exception('Error connecting server')
            core.events.server_refused.emit(None)

    def disconnect(self) -> None:
        if self.state != 'connected':
            return

        self.state = 'dying'
        ep, recv, beater = self._ep, self._recv_gr, self._beater_gr
        self._ep = None
        self._recv_gr = None
        self._beater_gr = None
        ep and ep.close()
        recv and recv.kill()
        beater and beater.kill()
        self.state = 'initial'

    def write(self, v: wire.ClientToServer) -> None:
        ep = self._ep
        if ep:
            ep.write(v)
        else:
            raise Exception('No endpoint present')

    def raw_write(self, v: bytes) -> None:
        ep = self._ep
        if ep:
            ep.raw_write(v)
        else:
            raise Exception('No endpoint present')

    # ----- Methods -----
    def _recv(self) -> None:
        me = gevent.getcurrent()
        me.link_exception(self._dropped)
        core = self.core
        D = core.events.server_command
        assert self._ep
        for v in self._ep.messages(timeout=None):
            D[v.__class__].emit(v)

    def _dropped(self, _) -> None:
        core = self.core
        core.events.server_dropped.emit(None)

    def _beat(self) -> None:
        while self._ep:
            self._ep.write(wire.Beat())
            gevent.sleep(10)
