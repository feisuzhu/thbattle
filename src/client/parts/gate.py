# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, Literal, Optional, Sequence, TYPE_CHECKING, Tuple, TypedDict, cast, List
from urllib.parse import urlparse
import logging
import socket
from functools import partial

# -- third party --
from gevent.event import Event
from gevent.lock import RLock
from gevent import getcurrent
import msgpack

# -- own --
from client.base import Game
from game.base import EventHandler, InputTransaction, Inputlet
import wire

# -- typing --
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
        self.input_sessions: Dict[int, dict] = {}

        # FIXME: ui_meta is currently a THB concept but this hook is game agnostic
        self.game_event_translator = cast(Any, g).ui_meta.event_translator

    def evt_user_input(self, arg: Tuple[InputTransaction, Inputlet]) -> Tuple[InputTransaction, Inputlet]:
        evt = Event()
        g, core = self.game, self.core

        trans, ilet = arg

        self.input_sessions[id(trans)]['done'] = evt.set

        core.gate.post('game.input', {
            'gid': core.game.gid_of(g),
            'tag': ilet.tag(),
            'trans_id': id(trans),
            'actor': ilet.actor.get_player().pid,
            'timeout': ilet.timeout,
        })
        evt.wait()

        return arg

    def handle(self, evt: str, arg: Any) -> Any:
        g, core = self.game, self.core

        if evt == 'user_input':
            self.evt_user_input(arg)

        elif evt == 'user_input_transaction_begin':
            env = dict(core.gate.eval_environ)
            env['trans'] = arg
            self.input_sessions[id(arg)] = env

            core.gate.post("game.input.trans:begin", {
                'gid': core.game.gid_of(g),
                'id': id(arg),
                'name': arg.name,
                'involved': [e.get_player().pid for e in arg.involved],
            })

        elif evt == 'user_input_transaction_end':
            core.gate.post("game.input.trans:end", {
                'gid': core.game.gid_of(g),
                'id': id(arg),
                'name': arg.name,
                'involved': [e.get_player().pid for e in arg.involved],
            })
            # core.gate.barrier()
            self.input_sessions.pop(id(arg), '')

        elif evt == 'user_input_start':
            trans, ilet = arg
            self.input_sessions[id(trans)]['ilet'] = ilet
            core.gate.post("game.input:start", {
                'id': id(ilet),
                'tag': ilet.tag(),
                'trans_id': id(trans),
                'trans_name': trans.name,
                'actor': ilet.actor.get_player().pid,
                'timeout': ilet.timeout,
            })
            self.game_event_translator(g, core, evt, arg)

        elif evt == 'user_input_finish':
            trans, ilet, rst = arg
            core.gate.post("game.input:finish", {
                'id': id(ilet),
                'tag': ilet.tag(),
                'trans_id': id(trans),
                'trans_name': trans.name,
                'actor': ilet.actor.get_player().pid,
                'timeout': ilet.timeout,
            })
            self.game_event_translator(g, core, evt, arg)

        elif evt == 'user_input_transaction_feedback':
            trans, ev, data = arg
            core.gate.post(f"game.input.trans:feedback:{ev}", {
                'id': id(trans),
                **data,
            })

        elif evt == '__game_live':
            # TODO: not working
            self.live = True
            return None
        else:
            self.game_event_translator(g, core, evt, arg)

        return arg


class CoreCall(TypedDict):
    call_id: int
    environ: Literal['input', 'core']
    method: str
    args: list
    as_ref: bool


class Gate(object):
    sock: socket.socket

    def __init__(self, core: Core, testing: bool = False):
        self.core = core
        self.current_game: Optional[Game] = None

        self.testing = testing
        if not testing:
            self.connected = False
            self.writelock = RLock()
            core.tasks['gate/connect'] = self.connect
        else:
            self.connected = True

        def setv(name: str, v: Any) -> None:
            self.eval_environ[name] = eval(v, self.eval_environ)

        self.eval_environ: Any = {
            'core': core,
            'set': setv,
            'partial': partial,
        }

        self.refs: Dict[int, Any] = {}
        self.ref_id = 1

        core.events.server_connected     += self.on_server_connected
        core.events.server_refused       += self.on_server_refused
        core.events.server_dropped       += self.on_server_dropped
        core.events.version_mismatch     += self.on_version_mismatch
        core.events.server_error         += self.on_server_error
        core.events.server_info          += self.on_server_info
        core.events.lobby_users          += self.on_lobby_users
        core.events.lobby_games          += self.on_lobby_games
        core.events.observe_request      += self.on_observe_request
        core.events.observer_enter       += self.on_observer_enter
        core.events.observer_leave       += self.on_observer_leave
        core.events.game_joined          += self.on_game_joined
        core.events.player_presence      += self.on_player_presence
        core.events.game_left            += self.on_game_left
        # core.events.room_users           += self.on_room_users  # Direct forward server message
        core.events.game_started         += self.on_game_started
        core.events.game_crashed         += self.on_game_crashed
        core.events.client_game_finished += self.on_client_game_finished
        core.events.game_ended           += self.on_game_ended
        core.events.auth_success         += self.on_auth_success
        core.events.auth_error           += self.on_auth_error

        D = core.events.server_command
        D[wire.InviteRequest] += self.handle_invite_request
        D[wire.KickRequest]   += self.handle_kick_request
        D[wire.SystemMsg]     += self.handle_system_msg
        D[wire.GameParams]    += self.handle_game_params
        D[wire.SetGameParam]  += self.handle_set_game_param
        D[wire.StartMatching] += self.handle_start_matching
        D[wire.RoomUsers]     += self.handle_room_users

    def post(self, op: str, data: Any) -> None:
        if not self.connected:
            log.debug('Attempt to post message when gate is not conected: %s -> %s', op, data)
            return

        b = msgpack.packb(data, use_bin_type=True)
        payload = msgpack.packb({'op': op, 'payload': b})

        if self.testing:
            log.debug('Posted to gate: %s -> %s', op, data)
            return

        log.debug('Posted to gate: %s -> %s', op, msgpack.unpackb(b))

        with self.writelock:
            self.sock.sendall(payload)

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
            # s.write = s.sendall
            u = self.unpacker = msgpack.Unpacker(s, raw=False)

            log.info('Gate is now connected to the shell')

            for msg in u:
                # {'op': 'xxx', 'v': Any}
                log.debug('core msg: %s', repr(msg))
                op, v = msg

                if op == 'call':
                    self.do_call(v)
                elif op == 'exec':
                    self.do_exec(v)

            core.result.set('gate_collapsed')

        except Exception as e:
            core.crash(e)
            return
        finally:
            self.connected = False

            try:
                s.close()
            except Exception:
                pass

    # ----- RPCs -----
    def do_call(self, call: CoreCall) -> None:
        env = None
        if call['environ'].startswith('input:'):
            if (g := self.current_game) and (ob := g.event_observer):
                assert isinstance(ob, UnityUIEventHook)
                env = ob.input_sessions.get(int(call['environ'][6:]))
                getcurrent().game = g
        elif call['environ'] == 'core':
            env = self.eval_environ

        ret = None
        if env is not None:
            args = call['args']
            for i, v in enumerate(args):
                if isinstance(v, msgpack.ExtType):
                    if v.code == 66:
                        args[i] = self.refs[int.from_bytes(v.data, byteorder='little')]
                    else:
                        raise Exception("Invalid ExtType")

            ret = eval(call['method'], env)(*args)

        if cid := call.get('call_id'):
            if call['as_ref']:
                ret = self._new_ref(ret)

            log.debug('call resp: %s -> %s', cid, ret)
            self.post('call_response', {
                'call_id': cid,
                'result': msgpack.packb(ret, use_bin_type=True),
            })

    def do_exec(self, v: str) -> None:
        exec(v, self.eval_environ)

    def _new_ref(self, v: Any) -> msgpack.ExtType:
        ref_id = self.ref_id
        self.ref_id += 1
        self.refs[ref_id] = v
        return msgpack.ExtType(66, ref_id.to_bytes(4, 'little'))

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

    def on_lobby_users(self, v: Sequence[wire.model.User]) -> Any:
        self.post("lobby_users", v)
        return v

    def on_lobby_games(self, v: Sequence[wire.model.Game]) -> Any:
        self.post("lobby_games", v)
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
        mode = g.__class__.__name__
        self.current_game = g

        self.eval_environ['g'] = g

        # <HACK: cross abstraction boundary>
        from thb.meta import view
        self.eval_environ['view'] = view
        # </HACK>

        meta = {
            'gid': core.game.gid_of(g),
            'type': mode,
        }

        self.post("game_joined", meta)
        return g

    def on_set_game_param(self, v: wire.SetGameParam) -> wire.SetGameParam:
        self.post("set_game_param", v)
        return v

    def on_player_presence(self, v: Tuple[Game, List[Tuple[int, wire.PresenceState]]]) -> Any:
        core = self.core
        g, presence = v
        self.post("player_presence", {
            'gid': core.game.gid_of(g),
            'presence': presence,
        })
        return v

    def on_game_left(self, g: Game) -> Game:
        core = self.core
        self.eval_environ.pop('g', '')
        self.current_game = None
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
        self.current_game = g
        if not g.event_observer:
            log.info('core.gate: Not installing event hook')
            g.event_observer = UnityUIEventHook(core, g)

        self.post("game_started", {
            'gid': core.game.gid_of(g),
            'type': g.__class__.__name__,
            'me': core.game.theone_of(g).pid,
            'pids': [p.pid for p in core.game.players_of(g)],
        })
        return g

    def on_game_crashed(self, g: Game) -> Game:
        core = self.core
        self.current_game = None
        self.post("game_crashed", core.game.gid_of(g))
        return g

    def on_client_game_finished(self, g: Game) -> Game:
        core = self.core
        self.current_game = None
        self.post("client_game_finished", core.game.gid_of(g))
        return g

    def on_game_ended(self, g: Game) -> Game:
        core = self.core
        self.post("game_ended", core.game.gid_of(g))
        return g

    def on_auth_success(self, pid: int) -> int:
        self.post("auth_success", pid)
        return pid

    def on_auth_error(self, v: str) -> str:
        self.post("auth_error", v)
        return v

    def handle_invite_request(self, m: wire.InviteRequest) -> wire.InviteRequest:
        self.post('invite_request', m.encode())
        return m

    def handle_kick_request(self, m: wire.KickRequest) -> wire.KickRequest:
        self.post('kick_request', m.encode())
        return m

    def handle_system_msg(self, m: wire.SystemMsg) -> wire.SystemMsg:
        self.post('system_msg', m.msg)
        return m

    def handle_game_params(self, m: wire.GameParams) -> wire.GameParams:
        self.post('game_params', m.encode())
        return m

    def handle_set_game_param(self, m: wire.SetGameParam) -> wire.SetGameParam:
        self.post('set_game_param', m.encode())
        return m

    def handle_start_matching(self, m: wire.StartMatching) -> wire.StartMatching:
        self.post('start_matching', m.modes)
        return m

    def handle_room_users(self, ev: wire.RoomUsers) -> wire.RoomUsers:
        self.post('room_users', ev.encode())
        return ev

    # ----- Methods -----
    def ignite(self) -> None:
        core = self.core
        assert self.current_game, 'No current game'
        core.game.start_game(self.current_game)

    def barrier(self) -> None:
        evt = Event()
        self.eval_environ['cross_barrier'] = evt.set
        self.post('barrier', 0)
        evt.wait()

    def invalidate_ref(self, ref_id: int) -> None:
        self.refs.pop(ref_id, '')


class MockGate(object):

    def __init__(self, core: Core):
        self.core = core

    def post(self, op: str, data: Any) -> None:
        pass
