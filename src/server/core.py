# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Any, Callable, Dict, Tuple, Type, TypeVar, cast

# -- third party --
from gevent.event import AsyncResult
from gevent.greenlet import Greenlet
from gevent.pool import Pool

# -- own --
from . import parts
from .base import Game
from .endpoint import Client
from game.base import Packet
from utils.events import EventHub
import wire


# -- code --
class Options(object):
    def __init__(self, options: Dict[str, Any]):
        self.node         = options.get('node', 'localhost')  # Current node name
        self.listen       = options.get('listen', '')         # Listen
        self.backend      = options.get('backend', '')        # Backend URI
        self.interconnect = options.get('interconnect', '')   # URI of chat server
        self.archive_path = options.get('archive_path', '')   # file:// URI of dir for storing game archives
        self.disables     = options.get('disables', [])       # disabled core components, will assign a None value


T = TypeVar('T', bound=wire.Message)


class _ClientCommandMapping:
    def __getitem__(self, k: Type[T]) -> EventHub[Tuple[Client, T]]:
        ...


class Events(object):
    def __init__(self, core: Core) -> None:
        self.core = core

        # ev = (core: Core)
        self.core_initialized = EventHub[Core]()

        # Fires when user state changes,
        # ev = (c: Client, from: str, to: str)
        self.user_state_transition = EventHub[Tuple[Client, str, str]]()

        # Client connected
        self.client_connected = EventHub[Client]()

        # Client dropped(connection lost)
        self.client_dropped = EventHub[Client]()

        # Client logged in when previous login still online, or still in active game
        # ev = c: Client  # old client obj with new connection `pivot_to`ed to it
        self.client_pivot = EventHub[Client]()

        # Client send some command
        # ev = (c: Client, args: (...))
        self.client_command: _ClientCommandMapping = \
            cast(_ClientCommandMapping, defaultdict(lambda: EventHub()))

        # Game is created
        # ev = g: Game
        self.game_created = EventHub[Game]()

        # Sent client game data
        self.game_data_send = EventHub[Tuple[Game, Client, Packet]]()

        # Received client game data
        self.game_data_recv = EventHub[Tuple[Game, Client, Packet]]()

        # Fires after old game ended and new game created.
        # Actors should copy settings from old to new
        # ev = (old: Game, g: Game)
        self.game_successive_create = EventHub[Tuple[Game, Game]]()

        # Game started running
        # ev = (g: Game)
        self.game_started = EventHub[Game]()

        # Client joined a game
        # ev = (g: Game, c: Client)
        self.game_joined = EventHub[Tuple[Game, Client]]()

        # Client left a game
        # ev = (g: Game, c: Client)
        self.game_left = EventHub[Tuple[Game, Client]]()

        # Game was ended, successfully or not.
        # ev = (g: Game)
        self.game_ended = EventHub[Game]()

        # Game ended in half way.
        # This fires before GAME_ENDED
        # ev = (g: Game)
        self.game_aborted = EventHub[Game]()

    def __setattr__(self, name, v):
        if hasattr(v, 'name'):
            v.name = f'{repr(self.core)}::{name}'
        object.__setattr__(self, name, v)


class Core(object):
    auto_id = 0

    def __init__(self, **options: Dict[str, Any]):
        self._auto_id = Core.auto_id
        Core.auto_id += 1

        self._result = AsyncResult()
        self.runner: CoreRunner = None
        self.tasks: Dict[str, Callable[[], None]] = {}

        self.options = Options(options)
        self.events = Events(self)
        self.tasks = {}

        self.initialize_parts()

        self.events.core_initialized.emit(self)

    def __repr__(self) -> str:
        return f'Core[S{self._auto_id}]'

    @property
    def result(self):
        return self._result

    def exception(self, e):
        self._result.set_exception(e)

    def initialize_parts(self):
        disables = self.options.disables

        if 'serve' not in disables:
            self.serve = parts.serve.Serve(self)

        if 'auth' not in disables:
            self.auth = parts.auth.Auth(self)

        if 'lobby' not in disables:
            self.lobby = parts.lobby.Lobby(self)

        if 'room' not in disables:
            self.room = parts.room.Room(self)

        if 'game' not in disables:
            self.game = parts.game.Game(self)

        if 'observe' not in disables:
            self.observe = parts.observe.Observe(self)

        if 'invite' not in disables:
            self.invite = parts.invite.Invite(self)

        if 'item' not in disables:
            self.item = parts.item.Item(self)

        if 'reward' not in disables:
            self.reward = parts.reward.Reward(self)

        if 'match' not in disables:
            self.match = parts.match.Match(self)

        if 'admin' not in disables:
            self.admin = parts.admin.Admin(self)

        if 'kedama' not in disables:
            self.kedama = parts.kedama.Kedama(self)

        if 'archive' not in disables:
            self.archive = parts.archive.Archive(self)

        if 'hooks' not in disables:
            self.hooks = parts.hooks.Hooks(self)

        if 'connect' not in disables:
            self.connect = parts.connect.Connect(self)

        if 'backend' not in disables:
            self.backend = parts.backend.Backend(self)

        if 'log' not in disables:
            self.log = parts.log.Log(self)

        if 'stats' not in disables:
            self.stats = parts.stats.Stats(self)

        if 'view' not in disables:
            self.view = parts.view.View(self)


class CoreRunner(object):
    def __init__(self, core: Core):
        self.core = core
        self.tasks: Dict[str, Greenlet] = {}

    def run(self) -> Any:
        core = self.core
        assert core.runner is None

        core.runner = self
        self.pool = pool = Pool()

        try:
            for k, f in core.tasks.items():
                gr = pool.spawn(f)
                gr.gr_name = k
                self.tasks[k] = gr

            return core.result.get()
        finally:
            self.pool.kill()

    def spawn(self, fn, *args, **kw):
        return self.pool.spawn(fn, *args, **kw)

    def shutdown(self) -> None:
        self.pool.kill()
