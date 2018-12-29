# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import TYPE_CHECKING, Any
import json
import logging

# -- third party --
import gevent
import websocket

# -- own --
from utils.misc import throttle

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Interconnect')


class Connect(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.game_created += self.refresh_status
        core.events.game_started += self.refresh_status
        core.events.game_ended += self.refresh_status
        core.events.game_aborted += self.refresh_status
        core.events.user_state_transition += self.refresh_status

        self._wsconn = websocket.create_connection(core.options.interconnect)

        self._wshandler = gevent.spawn(self._websocket_handler)
        self._wshb = gevent.spawn(self._websocket_heartbeat)

    def __repr__(self) -> str:
        return self.__class__.__name__

    @throttle(1.5)
    def refresh_status(self, ev: Any) -> Any:
        core = self.core
        self._wssend({
            'op': 'Message',
            'arg': {
                'entity': 'Interconnect',
                'channel': 'users',
                'text': json.dumps([
                    core.view.User(u)
                    for u in core.lobby.all_users()
                ]),
            }
        })

        return ev

    # ----- Public Methods -----
    def speaker(self, name: str, text: str) -> None:
        core = self.core
        self._wssend({
            'op': 'Message',
            'arg': {
                'entity': 'Speaker',
                'channel': core.options.node,
                'text': text,
            }
        })

    # ----- Methods -----
    def _websocket_handler(self) -> None:
        ws = self._wsconn
        while ws.connected:
            try:
                r = json.loads(ws.recv())
                self._wsrecv(r)
            except Exception as e:
                log.exception(e)
                gevent.sleep(1)

    def _websocket_heartbeat(self) -> None:
        ws = self._wsconn
        while ws.connected:
            try:
                gevent.sleep(30)
                ws.ping()
            except Exception as e:
                log.exception(e)

    def _wssend(self, v: Any) -> None:
        self._wsconn.send(json.dumps(v))

    def _wsrecv(self, v: Any) -> None:
        pass
