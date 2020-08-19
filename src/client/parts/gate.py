# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Callable, Dict, Sequence, TYPE_CHECKING, Tuple, Optional
from urllib.parse import urlparse
import logging
import random
import socket
import sys

# -- third party --
from gevent.event import Event
from gevent.lock import RLock
from mypy_extensions import TypedDict
from typing_extensions import Literal
import gevent
import gevent.hub
import msgpack

# -- own --
from client.base import Game
from game.base import EventHandler, Player
import wire


# -- code --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('parts.gate.Gate')


class UnityUIEventHook(EventHandler):
    game: Game

    def __init__(self, core: Core, g: Game):
        EventHandler.__init__(self, g)
        self.core = core
        self.game = g
        self.gid = core.game.gid_of(g)
        self.input_done: Optional[Event] = None

    def evt_user_input(self, arg: Tuple[InputTransaction, Inputlet]) -> Tuple[InputTransaction, Inputlet]:
        evt = Event()
        self.input_done = evt
        g, core = self.game, self.core

        core.gate.post('game_input', {
            'type': 'input',
            'gid': self.gid,

            {'t': 'i', 'g': g, 'arg': arg, 'done': evt.set})
        })

        try:
            evt.wait()
        finally:
            self.input_done = None

    def handle(self, evt: str, arg: Any) -> Any:
        g, core = self.game, self.core

        if evt == 'user_input':
            self.evt_user_input(arg)
        elif evt == '__game_live':
            self.live = True
            return None
        else:
            core.warpgate.feed_ev({'t': 'g', 'g': g, 'evt': evt, 'arg': arg})

        if random.random() < 0.01:
            core.runner.idle()

        return arg

# g.event_observer = UnityUIEventHook(self.warpgate, g)

class Gate(object):
    def __init__(self, core: Core):
        self.core = core

        self.connected = False
        self.writelock = RLock()

        self.eval_environ: Any = {
            'core': core
        }

        core.tasks['gate/connect'] = self.connect

        core.events.server_connected     += self.on_server_connected
        core.events.server_refused       += self.on_server_refused
        core.events.server_dropped       += self.on_server_dropped
        core.events.version_mismatch     += self.on_version_mismatch
        core.events.server_error         += self.on_server_error
        core.events.server_info          += self.on_server_info
        core.events.lobby_updated        += self.on_lobby_updated
        core.events.observe_request      += self.on_observe_request
        core.events.observer_enter       += self.on_observer_enter
        core.events.observer_leave       += self.on_observer_leave
        core.events.game_joined          += self.on_game_joined
        core.events.player_presence      += self.on_player_presence
        core.events.game_left            += self.on_game_left
        core.events.room_users           += self.on_room_users
        core.events.game_started         += self.on_game_started
        core.events.game_crashed         += self.on_game_crashed
        core.events.client_game_finished += self.on_client_game_finished
        core.events.game_ended           += self.on_game_ended
        core.events.auth_success         += self.on_auth_success
        core.events.auth_error           += self.on_auth_error

    def connect(self) -> None:
        core = self.core
        uri = core.options.gate_uri
        uri = urlparse(uri)
        assert uri.scheme == 'tcp'

        s: Any = socket.socket()
        try:
            s.connect((uri.hostname, uri.port))

            self.connected = True
            self.sock = s

            s.read = s.recv
            s.write = s.sendall
            u = self.unpacker = msgpack.Unpacker(s, raw=False)

            for msg in u:
                # {'op': 'xxx', 'v': Any}
                op, v = msg

                if op == 'eval':
                    self.do_eval(v)

        except Exception as e:
            core.crash(e)
            return

        core.crash(Exception('Gate closed'))

    def post(self, op: str, data: Any) -> None:
        if not self.connected:
            return

        b = msgpack.packb(data, use_bin_type=True)
        payload = msgpack.packb({'op': op, 'payload': b})
        with self.writelock:
            self.sock.sendall(payload)

    # ----- RPCs -----
    def do_eval(self, v: str) -> None:
        pass

    # ----- Handlers -----
    def on_server_connected(self, v: bool) -> bool:
        self.post("server_connected", v)
        return v

    def on_server_refused(self, v: bool) -> bool:
        self.post("server_refused", v)
        return v

    def on_server_dropped(self, v: bool) -> bool:
        self.post("server_dropped", v)
        return v

    def on_version_mismatch(self, v: bool) -> bool:
        self.post("version_mismatch", v)
        return v

    def on_server_error(self, v: str) -> str:
        self.post("server_error", v)
        return v

    def on_server_info(self, v: str) -> str:
        self.post("server_info", v)
        return v

    def on_lobby_updated(self, v: Tuple[Sequence[wire.model.User], Sequence[wire.model.Game]]) -> Any:
        ul, gl = v
        self.post("lobby_updated", {
            'users': ul,
            'games': gl,
        })
        return v

    def on_observe_request(self, v: int) -> int:
        self.post("observe_request", v)
        return v

    def on_observer_enter(self, v: Tuple[int, int]) -> Tuple[int, int]:
        self.post("observer_enter", {
            'observer': v[0],
            'observee': v[1],
        })
        return v

    def on_observer_leave(self, v: Tuple[int, int]) -> Tuple[int, int]:
        self.post("observer_leave", {
            'observer': v[0],
            'observee': v[1],
        })
        return v

    def on_game_joined(self, g: Game) -> Game:
        core = self.core
        self.post("game_joined", core.game.gid_of(g))
        return g

    def on_set_game_param(self, v: wire.SetGameParam) -> wire.SetGameParam:
        self.post("set_game_param", v)
        return v

    def on_player_presence(self, v: Tuple[Game, Dict[Player, bool]]) -> Any:
        core = self.core
        g, pd = v
        self.post("player_presence", {
            'gid': core.game.gid_of(g),
            'players': [{
                'uid': p.uid,
                'present': b,
            } for p, b in pd.items()]
        })
        return v

    def on_game_left(self, g: Game) -> Game:
        core = self.core
        self.post("game_left", core.game.gid_of(g))
        return g

    def on_room_users(self, v: Tuple[Game, Sequence[wire.model.User]]) -> Any:
        core = self.core
        g, ul = v
        self.post("room_users", {
            'gid': core.game.gid_of(g),
            'users': ul,
        })
        return v

    def on_game_started(self, g: Game) -> Game:
        core = self.core
        self.post("game_started", core.game.gid_of(g))
        return g

    def on_game_crashed(self, g: Game) -> Game:
        core = self.core
        self.post("game_crashed", core.game.gid_of(g))
        return g

    def on_client_game_finished(self, g: Game) -> Game:
        core = self.core
        self.post("client_game_finished", core.game.gid_of(g))
        return g

    def on_game_ended(self, g: Game) -> Game:
        core = self.core
        self.post("game_ended", core.game.gid_of(g))
        return g

    def on_auth_success(self, uid: int) -> int:
        self.post("auth_success", uid)
        return uid

    def on_auth_error(self, v: str) -> str:
        self.post("auth_error", v)
        return v
