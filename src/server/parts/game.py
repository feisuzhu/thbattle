# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type
import logging
import random

# -- third party --
from gevent.event import AsyncResult
from mypy_extensions import TypedDict

# -- own --
from game.base import GameArchive, GameData, Player, BootstrapAction, GameItem
from server.base import Game as ServerGame, HumanPlayer, NPCPlayer
from server.endpoint import Client
from server.utils import command
from utils.misc import BatchList
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Game')


class GameAssocOnClient(TypedDict):
    game: Optional[ServerGame]
    params: Dict[str, Any]


def Au(self: GamePart, u: Client) -> GameAssocOnClient:
    return u._[self]


class GameAssocOnGame(TypedDict):
    params: Dict[str, Any]
    players: BatchList[Player]
    fleed: Dict[Client, bool]
    aborted: bool
    crashed: bool
    rngseed: int
    data: Dict[Client, GameData]
    winners: List[Player]
    halt: Optional[AsyncResult]


def Ag(self: GamePart, g: ServerGame) -> GameAssocOnGame:
    return g._[self]


class GamePart(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.game_started += self.handle_game_started
        core.events.game_ended += self.handle_game_ended
        core.events.game_joined += self.handle_game_joined
        core.events.game_left += self.handle_game_left
        core.events.game_successive_create += self.handle_game_successive_create
        core.events.user_state_transition += self.handle_user_state_transition
        core.events.client_pivot += self.handle_client_pivot

        D = core.events.client_command
        D[wire.SetGameParam] += self._set_param
        D[wire.GameData] += self._gamedata

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        u, f, t = ev
        if t == 'lobby':
            u._[self] = GameAssocOnClient(game=None, params={})

        return ev

    def handle_client_pivot(self, u: Client) -> Client:
        core = self.core
        if core.lobby.state_of(u) == 'game':
            g = Au(self, u)['game']
            assert g
            assert u in core.room.users_of(g)

            u.write(wire.GameJoined(core.view.GameDetail(g)))
            u.write(wire.GameStarted(core.view.GameDetail(g)))

            self.replay(u, u)

        return u

    def handle_game_started(self, g: ServerGame) -> ServerGame:
        self._setup_game(g)

        core = self.core
        users = core.room.users_of(g)
        for u in users:
            u.write(wire.GameStarted(core.view.GameDetail(g)))

        return g

    def handle_game_ended(self, g: ServerGame) -> ServerGame:
        core = self.core
        users = core.room.online_users_of(g)
        for u in users:
            u.write(wire.GameEnded(core.room.gid_of(g)))

        return g

    def handle_game_joined(self, ev: Tuple[ServerGame, Client]) -> Tuple[ServerGame, Client]:
        g, u = ev
        core = self.core
        if core.room.is_started(g):
            Ag(self, g)['data'][u].revive()
            Ag(self, g)['fleed'][u] = False

        Au(self, u)['game'] = g

        return ev

    def handle_game_left(self, ev: Tuple[ServerGame, Client]) -> Tuple[ServerGame, Client]:
        g, u = ev
        core = self.core
        if core.room.is_started(g):
            Ag(self, g)['data'][u].die()
            uid = core.auth.uid_of(u)
            p = next(i for i in Ag(self, g)['players'] if i.uid == uid)
            Ag(self, g)['fleed'][u] = bool(g.can_leave(p))

        Au(self, u)['game'] = None

        return ev

    def handle_game_successive_create(self, ev: Tuple[ServerGame, ServerGame]) -> Tuple[ServerGame, ServerGame]:
        old, g = ev
        core = self.core

        params = Ag(self, old)['params']
        Ag(self, g)['params'] = params
        gid = core.room.gid_of(g)
        core.room.online_users_of(old).write(wire.GameParams(gid=gid, params=params))

        return ev

    # ----- Commands -----
    @command('room')
    def _set_param(self, u: Client, ev: wire.SetGameParam) -> None:
        core = self.core

        if core.lobby.state_of(u) != 'room':
            return

        g = core.game.current(u)
        if not g:
            return None

        users = core.room.online_users_of(g)

        if core.room.gid_of(g) != ev.gid:
            log.error("Error setting game param, gid mismatch with user's current game")
            return

        cls = g.__class__
        if ev.key not in cls.params_def:
            log.error('Invalid option "%s"', ev.key)
            return

        if ev.value not in cls.params_def[ev.key]:
            log.error('Invalid value "%s" for key "%s"', ev.value, ev.key)
            return

        if Ag(self, g)['params'][ev.key] == ev.value:
            return

        Ag(self, g)['params'][ev.key] = ev.value

        gid = core.room.gid_of(g)

        for u in users:
            if core.lobby.state_of(u) == 'ready':
                core.room.cancel_ready(u)

            u.write(ev)
            u.write(wire.GameParams(gid, Ag(self, g)['params']))

    @command('game')
    def _gamedata(self, u: Client, ev: wire.GameData) -> None:
        core = self.core
        g = Au(self, u)['game']
        if not g:
            return None

        if ev.gid != core.room.gid_of(g):
            return

        pkt = Ag(self, g)['data'][u].feed_recv(ev.tag, ev.data)
        core.events.game_data_recv.emit((g, u, pkt))

    # ----- Private Methods -----
    def _setup_game(self, g: ServerGame) -> None:
        core = self.core
        users = core.room.users_of(g)
        gid = core.room.gid_of(g)

        Ag(self, g)['data'] = {
            u: GameData(gid) for u in users
        }
        Ag(self, g)['players'] = self._build_players(g, users)

    def _build_players(self, g: ServerGame, users: List[Client]) -> BatchList[Player]:
        core = self.core
        pl: BatchList[Player] = BatchList([HumanPlayer(g, core.auth.uid_of(u), u) for u in users])
        pl[:0] = [NPCPlayer(g, i.name, i.input_handler) for i in g.npc_players]

        return pl

    # ----- Public Methods -----
    def create_game(self, cls: Type[ServerGame]) -> ServerGame:
        g = cls()

        seed = random.getrandbits(63)
        g.random = random.Random(seed)

        g._[self] = GameAssocOnGame({
            'params': {k: v[0] for k, v in cls.params_def.items()},
            'players': BatchList(),
            'fleed': defaultdict(bool),
            'aborted': False,
            'crashed': False,
            'rngseed': seed,
            'data': {},
            'winners': [],
            'halt': None,
        })

        return g

    def halt_on_start(self, g: ServerGame) -> None:
        "For testing"
        g._[self]['halt'] = AsyncResult()

    def should_halt(self, g: ServerGame) -> bool:
        "For testing"
        return bool(g._[self]['halt'])

    def get_bootstrap_action(self, g: ServerGame) -> BootstrapAction:
        "For testing"
        rst = g._[self]['halt']
        if not rst:
            raise Exception('Game will not halt')

        return rst.get()

    def set_bootstrap_action(self, g: ServerGame, act: BootstrapAction) -> None:
        "For testing"
        rst = g._[self]['halt']
        if not rst:
            raise Exception('Game will not halt')

        rst.set(act)

    def replay(self, u: Client, to: Client) -> None:
        core = self.core
        g = Au(self, u)['game']
        assert g
        pkts = Ag(self, g)['data'][u].get_sent()
        if not pkts:
            return

        gid = core.room.gid_of(g)

        to.write_bulk([
            wire.GameData(gid, p.tag, p.data)
            for p in pkts
        ])
        to.write(wire.GameData(gid, "__game_live", None))

    def mark_crashed(self, g: ServerGame) -> None:
        Ag(self, g)['crashed'] = True

    def is_crashed(self, g: ServerGame) -> bool:
        return Ag(self, g)['crashed']

    def abort(self, g: ServerGame) -> None:
        core = self.core
        Ag(self, g)['aborted'] = True
        core.events.game_aborted.emit(g)

    def is_aborted(self, g: ServerGame) -> bool:
        return Ag(self, g)['aborted']

    def is_fleed(self, g: ServerGame, u: Client) -> bool:
        return Ag(self, g)['fleed'][u]

    def get_gamedata_archive(self, g: ServerGame) -> List[GameArchive]:
        core = self.core
        ul = core.room.users_of(g)
        return [
            Ag(self, g)['data'][u].archive() for u in ul
        ]

    def write(self, g: ServerGame, u: Client, tag: str, data: object) -> None:
        core = self.core
        assert Au(self, u)['game'] is g
        pkt = Ag(self, g)['data'][u].feed_send(tag, data)
        gid = core.room.gid_of(g)
        u.write(wire.GameData(gid=gid, tag=tag, data=data))
        core.events.game_data_send.emit((g, u, pkt))

    def current(self, u: Client) -> Optional[ServerGame]:
        g = Au(self, u)['game']
        return g

    def set_winners(self, g: ServerGame, winners: List[Player]) -> None:
        Ag(self, g)['winners'] = winners

    def params_of(self, g: ServerGame) -> Dict[str, Any]:
        return Ag(self, g)['params']

    def winners_of(self, g: ServerGame) -> List[Player]:
        return Ag(self, g)['winners']

    def rngseed_of(self, g: ServerGame) -> int:
        return Ag(self, g)['rngseed']

    def gamedata_of(self, g: ServerGame, u: Client) -> GameData:
        return Ag(self, g)['data'][u]

    def players_of(self, g: ServerGame) -> BatchList[Player]:
        return Ag(self, g)['players']
