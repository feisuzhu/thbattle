# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Optional, TYPE_CHECKING, Any
from urllib.parse import urlparse
import logging
import socket

# -- third party --
from gevent import Greenlet
import gevent

# -- own --
from endpoint import Endpoint, EndpointDied
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
        D[wire.Info] += self._info
        D[wire.Error] += self._error

    def _greeting(self, ev: wire.Greeting) -> wire.Greeting:
        from settings import VERSION

        core = self.core

        if ev.version != VERSION:
            self.disconnect()
            core.events.version_mismatch.emit(True)
        else:
            self.server_name = ev.node
            core.events.server_connected.emit(True)

        return ev

    def _ping(self, ev: wire.Ping) -> wire.Ping:
        self.write(wire.Pong())
        return ev

    def _info(self, ev: wire.Info) -> wire.Info:
        core = self.core
        core.events.server_info.emit(ev.msg)
        return ev

    def _error(self, ev: wire.Error) -> wire.Error:
        log.warning('ServerError: %s', ev.msg)
        core = self.core
        core.events.server_error.emit(ev.msg)
        return ev

    # ----- Public Methods -----
    def connect(self, uri: str) -> None:
        core = self.core

        log.info('Connecting to %s', uri)

        uri = urlparse(uri)
        assert uri.scheme == 'tcp'

        if not self.state == 'initial':
            return

        try:
            self.state = 'connecting'
            assert uri.port
            addr = uri.hostname, uri.port
            s = socket.create_connection(addr)
            self._ep = Endpoint(s, addr)
            self._recv_gr = core.runner.spawn(self._recv)
            self._beater_gr = core.runner.spawn(self._beat)
            self.state = 'connected'
        except Exception:
            self.state = 'initial'
            log.exception('Error connecting server')
            core.events.server_refused.emit(True)

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
        core = self.core
        me = gevent.getcurrent()
        me.link_exception(self._dropped)
        me.gr_name = f'{core}::RECV'
        D = core.events.server_command

        assert self._ep
        try:
            for v in self._ep.messages(timeout=None):
                D[v.__class__].emit(v)
        except EndpointDied:
            pass

        core.events.server_dropped.emit(True)

    def _dropped(self, _: Any) -> None:
        core = self.core
        core.events.server_dropped.emit(True)

    def _beat(self) -> None:
        core = self.core
        if core.options.testing:
            return

        while self._ep:
            self._ep.write(wire.Beat())
            core.runner.sleep(10)
