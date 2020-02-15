# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Any, Dict, Sequence, Tuple, Type, TypeVar, cast

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
        self.disables = options.get('disables', [])
        self.paranoid = options.get('paranoid', False)    # For unit test


T = TypeVar('T')


class _ServerCommandMapping(dict):
    __slots__ = ('core',)

    def __init__(self, core: Core):
        self.core = core
        super().__init__()

    def __getitem__(self, k: Type[T]) -> EventHub[T]:
        if k in self:
            return dict.__getitem__(self, k)

        hub = EventHub()
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
        self.server_connected = EventHub[None]()

        # Server timed-out or actively rejects
        self.server_refused = EventHub[None]()

        # Server dropped
        self.server_dropped = EventHub[None]()

        # Server & client version mismatch
        self.version_mismatch = EventHub[None]()

        # Lobby status
        self.lobby_updated = EventHub[Tuple[Sequence[wire.model.User], Sequence[wire.model.Game]]]()

        # Observer state
        self.observer_enter = EventHub[wire.ObserverEnter]()
        self.observer_leave = EventHub[wire.ObserverLeave]()

        # Joined a game
        self.game_joined = EventHub[Game]()

        # Player presence changed
        self.player_presence = EventHub[Tuple[Game, Dict[Player, bool]]]()

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

        # ev = uid: int
        self.auth_success = EventHub[int]()

        # ev = reason: str
        self.auth_error = EventHub[str]()

    def __setattr__(self, name, v):
        if hasattr(v, 'name'):
            v.name = f'{repr(self.core)}::{name}'
        object.__setattr__(self, name, v)


class Core(core.Core):
    core_type = 'C'

    def initialize(self, options: Dict[str, Any]) -> None:
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

        if 'game' not in disables:
            self.game = parts.game.GamePart(self)

        if 'replay' not in disables:
            self.replay = parts.replay.Replay(self)

        if 'warpgate' not in disables:
            self.warpgate = parts.warpgate.Warpgate(self)

        self.events.core_initialized.emit(self)
