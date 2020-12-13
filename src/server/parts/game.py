# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type, TypedDict
import logging
import random

# -- third party --
# -- own --
from endpoint import Endpoint
from game.base import GameArchive, GameData, Player
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


class GamePartAssocOnClient(TypedDict):
    game: Optional[ServerGame]
    params: Dict[str, Any]


def Au(self: GamePart, u: Client) -> GamePartAssocOnClient:
    return u._[self]


class GamePartAssocOnGame(TypedDict):
    params: Dict[str, Any]
    players: BatchList[Player]
    fled: Dict[Client, bool]
    aborted: bool
    crashed: bool
    rngseed: int
    data: Dict[Client, GameData]
    winners: List[Player]


def Ag(self: GamePart, g: ServerGame) -> GamePartAssocOnGame:
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
        D[wire.GameData] += self._gamedata

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        u, f, t = ev
        if t == 'lobby':
            u._[self] = GamePartAssocOnClient(game=None, params={})

        return ev

    def handle_client_pivot(self, u: Client) -> Client:
        core = self.core
        if core.lobby.state_of(u) == 'game':
            g = Au(self, u)['game']
            assert g

            pid = core.auth.pid_of(u)
            for p in Ag(self, g)['players']:
                if isinstance(p, HumanPlayer):
                    if core.auth.pid_of(p.client) == pid:
                        p.client = u

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

        self._notify_presence(g)
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
            Ag(self, g)['fled'][u] = False
            self._notify_presence(g)

        Au(self, u)['game'] = g

        return ev

    def handle_game_left(self, ev: Tuple[ServerGame, Client]) -> Tuple[ServerGame, Client]:
        g, u = ev
        core = self.core
        if core.room.is_started(g):
            Ag(self, g)['data'][u].die()
            pid = core.auth.pid_of(u)
            p = next(i for i in Ag(self, g)['players'] if i.pid == pid)
            Ag(self, g)['fled'][u] = bool(g.can_leave(p))
            self._notify_presence(g)

        Au(self, u)['game'] = None

        return ev

    def handle_game_successive_create(self, ev: Tuple[ServerGame, ServerGame]) -> Tuple[ServerGame, ServerGame]:
        old, g = ev
        core = self.core

        assert old.ended
        assert not g.ended

        params = Ag(self, old)['params']
        Ag(self, g)['params'] = params
        gid = core.room.gid_of(g)
        core.room.online_users_of(old).write(wire.GameParams(gid=gid, params=params))

        return ev

    # ----- Commands -----
    @command('game')
    def _gamedata(self, u: Client, ev: wire.GameData) -> None:
        core = self.core
        g = Au(self, u)['game']
        if not g:
            return None

        if ev.gid != core.room.gid_of(g):
            return

        pkt = Ag(self, g)['data'][u].feed_recv(ev.tag, ev.data)
        if pkt:
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
        pl: BatchList[Player] = BatchList([HumanPlayer(g, core.auth.pid_of(u), u) for u in users])
        pl[:0] = [NPCPlayer(g, core.auth.next_kedama_pid(), i.input_handler) for i in g.npc_players]

        return pl

    def _notify_presence(self, g: ServerGame) -> None:
        core = self.core
        rst = []
        for p in Ag(self, g)['players']:
            if isinstance(p, NPCPlayer):
                rst.append(wire.PresenceState.ONLINE)
            elif isinstance(p, HumanPlayer):
                if Ag(self, g)['fled'].get(p.client):
                    rst.append(wire.PresenceState.FLED)
                elif p.client.is_dead():
                    rst.append(wire.PresenceState.DROPPED)
                else:
                    rst.append(wire.PresenceState.ONLINE)
            else:
                raise Exception('WTF')

        ul = core.room.online_users_of(g)

        d = Endpoint.encode_bulk([wire.PlayerPresence(
            gid=core.room.gid_of(g),
            presence=rst,
        )])

        core.runner.spawn(ul.raw_write, d)

    # ----- Public Methods -----
    def create_game(self, cls: Type[ServerGame]) -> ServerGame:
        g = cls()

        seed = random.getrandbits(63)
        g.random = random.Random(seed)

        g._[self] = GamePartAssocOnGame({
            'params': {k: v[0] for k, v in cls.params_def.items()},
            'players': BatchList(),
            'fled': defaultdict(bool),
            'aborted': False,
            'crashed': False,
            'rngseed': seed,
            'data': {},
            'winners': [],
        })

        return g

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

    def mark_aborted(self, g: ServerGame) -> None:
        Ag(self, g)['aborted'] = True

    def is_aborted(self, g: ServerGame) -> bool:
        return Ag(self, g)['aborted']

    def is_fled(self, g: ServerGame, u: Client) -> bool:
        return Ag(self, g)['fled'][u]

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

    def set_param(self, g: ServerGame, key: str, value: Any) -> bool:
        if Ag(self, g)['params'][key] == value:
            return False

        Ag(self, g)['params'][key] = value
        return True

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
