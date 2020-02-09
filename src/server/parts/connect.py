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

        self._wsconn = None

        core.events.game_created += self.refresh_status
        core.events.game_started += self.refresh_status
        core.events.game_ended += self.refresh_status
        core.events.game_aborted += self.refresh_status
        core.events.user_state_transition += self.refresh_status

    def __repr__(self) -> str:
        return self.__class__.__name__

    def refresh_status(self, ev: Any) -> Any:
        self._refresh_status()
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
    @throttle(1.5)
    def _refresh_status(self) -> None:
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

    def _wssend(self, v: Any) -> None:
        core = self.core
        for i in range(3):
            try:
                conn = self._wsconn
                if not conn or not conn.connected:
                    conn = websocket.create_connection(core.options.interconnect)
                    self._wsconn = conn
                conn.send(json.dumps(v))
                return
            except Exception:
                log.exception('Error sending interconnect message')
                gevent.sleep(3)

        log.error('WebSocket send with multiple failed attempts, giving up, message: %s', v)
