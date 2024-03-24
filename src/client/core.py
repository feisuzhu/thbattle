# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, Sequence, Tuple, Type, TypeVar, List

# -- third party --
# -- own --
from client import parts
from client.base import Game
from game.base import Player
from utils.events import EventHub
import core
import wire


# -- code --
class Options(object):
    def __init__(self, options: Dict[str, Any]):
        self.gate_uri = options.get('gate_uri', 'tcp://127.0.0.1:23333')
        self.disables = options.get('disables', [])
        self.testing = options.get('testing', False)      # In tests?


T = TypeVar('T')


class _ServerCommandMapping(dict):
    __slots__ = ('core',)

    def __init__(self, core: Core):
        self.core = core
        super().__init__()

    def __getitem__(self, k: Type[T]) -> EventHub[T]:
        if k in self:
            return dict.__getitem__(self, k)

        hub = EventHub[T]()
        hub.name = f'{self.core}::server_command'
        self[k] = hub
        return hub


class Events(object):
    def __init__(self, core: Core) -> None:
        self.core = core

        self.core_initialized = EventHub[Core]()

        # Fires when server send some command
        self.server_command = _ServerCommandMapping(core)

        # Server connected
        self.server_connected = EventHub[bool]()

        # Server timed-out or actively rejects
        self.server_refused = EventHub[bool]()

        # Server dropped
        self.server_dropped = EventHub[bool]()

        # Server & client version mismatch
        self.version_mismatch = EventHub[bool]()

        # Server error
        self.server_error = EventHub[str]()

        # Server info
        self.server_info = EventHub[str]()

        # Lobby status
        self.lobby_users = EventHub[Sequence[wire.model.User]]()
        self.lobby_status = EventHub[wire.LobbyStatus]()

        # Observer request
        self.observe_request = EventHub[int]()

        # Observer state
        self.observer_enter = EventHub[Tuple[int, int]]()
        self.observer_leave = EventHub[Tuple[int, int]]()

        # Joined a game
        self.game_joined = EventHub[Game]()

        # Game param changed
        self.set_game_param = EventHub[wire.SetGameParam]()

        # Player presence changed
        self.player_presence = EventHub[Tuple[Game, List[Tuple[int, wire.PresenceState]]]]()

        # Left a game
        self.game_left = EventHub[Game]()

        # Left a game
        # ev = (g: Game, users: [server.core.view.User(u), ...])
        self.room_users = EventHub[Tuple[Game, Sequence[wire.model.User]]]()

        # Game is up and running
        # ev = (g: Game)
        self.game_started = EventHub[Game]()

        # ev = (g: Game)
        self.game_crashed = EventHub[Game]()

        # Client game finished,
        # Server will send `game_end` soon if everything goes right
        self.client_game_finished = EventHub[Game]()

        # ev = (g: Game)
        self.game_ended = EventHub[Game]()

        # ev = pid: int
        self.auth_success = EventHub[int]()

        # ev = reason: str
        self.auth_error = EventHub[str]()

    def __setattr__(self, name: str, v: Any) -> None:
        if hasattr(v, 'name'):
            v.name = f'{repr(self.core)}::{name}'
        object.__setattr__(self, name, v)


class Core(core.Core):
    core_type = 'C'

    def __init__(self, **options: Any) -> None:
        super().__init__()

        self.options = Options(options)
        self.events = Events(self)

        disables = self.options.disables

        if 'server' not in disables:
            self.server = parts.server.Server(self)

        if 'auth' not in disables:
            self.auth = parts.auth.Auth(self)

        if 'lobby' not in disables:
            self.lobby = parts.lobby.Lobby(self)

        if 'room' not in disables:
            self.room = parts.room.Room(self)

        if 'matching' not in disables:
            self.matching = parts.matching.Matching(self)

        if 'observe' not in disables:
            self.observe = parts.observe.Observe(self)

        if 'game' not in disables:
            self.game = parts.game.GamePart(self)

        if 'contest' not in disables:
            self.contest = parts.contest.Contest(self)

        if 'replay' not in disables:
            self.replay = parts.replay.Replay(self)

        if 'admin' not in disables:
            self.admin = parts.admin.Admin(self)

        if 'gate' not in disables:
            self.gate = parts.gate.Gate(self, testing=self.options.testing)
        else:
            self.gate = parts.gate.MockGate(self)  # type: ignore

        self.events.core_initialized.emit(self)
