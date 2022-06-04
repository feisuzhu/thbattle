# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type, TypedDict
import base64
import dataclasses
import datetime
import json
import logging
import random
import time
import zlib

# -- third party --
# -- own --
from endpoint import Endpoint
from game.base import GameData, Player
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
    fled: Dict[int, bool]
    aborted: bool
    crashed: bool
    rngseed: int
    data: Dict[int, GameData]
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
                    if p.pid == pid:
                        p.client = u

            u.write(wire.GameJoined(core.view.GameDetail(g)))
            u.write(wire.GameStarted(core.view.GameDetail(g)))

            self.replay(u, u)

            self._notify_presence(g)

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

        meta = self._meta(g)
        archive = self._archive(g)

        core.backend.query('''
            mutation ArchiveRewardRank($game: GameInput!, $archive: String!) {
                GmArchive(game: $game, archive: $archive) {
                    id
                }
                GmSettleRewards(game: $game) {
                    player { id }
                }
                RkAdjustRanking(game: $game) {
                    player { id }
                }
            }
        ''', meta=meta, archive=archive)

        users = core.room.online_users_of(g)
        for u in users:
            u.write(wire.GameEnded(core.room.gid_of(g)))

        return g

    def _meta(self, g: ServerGame) -> Dict[str, Any]:
        core = self.core
        start = core.room.start_time_of(g)

        flags = dict(dataclasses.asdict(core.room.flags_of(g)))
        flags['crashed'] = self.is_crashed(g)
        flags['aborted'] = self.is_aborted(g)

        return {
            'gameId': core.room.gid_of(g),
            'name': core.room.name_of(g),
            'type': g.__class__.__name__,
            'flags': flags,
            'players': [core.auth.pid_of(u) for u in core.room.users_of(g)],
            'winners': [core.auth.pid_of(p.client) for p in self.winners_of(g) if isinstance(p, HumanPlayer)],
            'deserters': [core.auth.pid_of(u) for u in core.room.users_of(g) if self.is_fled(g, u)],
            'startedAt': datetime.datetime.now().isoformat(),
            'duration': int(time.time() - start),
        }

    def _archive(self, g: ServerGame) -> str:
        from settings import VERSION

        core = self.core
        ul = core.room.users_of(g)
        data = [Ag(self, g)['data'][core.auth.pid_of(u)].archive() for u in ul]
        data = {
            'version': VERSION,
            'gid': core.room.gid_of(g),
            'class': g.__class__.__name__,
            'params': self.params_of(g),
            'items': core.item.item_skus_of(g),
            'rngseed': self.rngseed_of(g),
            'players': [core.auth.pid_of(u) for u in core.room.users_of(g)],
            'data': data,
        }

        return base64.b64encode(
            zlib.compress(json.dumps(data).encode('utf-8'))
        ).decode('utf-8')

    def handle_game_joined(self, ev: Tuple[ServerGame, Client]) -> Tuple[ServerGame, Client]:
        g, u = ev
        core = self.core
        pid = core.auth.pid_of(u)
        if core.room.is_started(g):
            Ag(self, g)['data'][pid].revive()
            Ag(self, g)['fled'][pid] = False
            self._notify_presence(g)

        Au(self, u)['game'] = g

        return ev

    def handle_game_left(self, ev: Tuple[ServerGame, Client]) -> Tuple[ServerGame, Client]:
        g, u = ev
        core = self.core
        if core.room.is_started(g):
            pid = core.auth.pid_of(u)
            Ag(self, g)['data'][pid].die()
            p = next(i for i in Ag(self, g)['players'] if i.pid == pid)
            Ag(self, g)['fled'][pid] = bool(g.can_leave(p))
            self._notify_presence(g)

        Au(self, u)['game'] = None

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

        pid = core.auth.pid_of(u)
        pkt = Ag(self, g)['data'][pid].feed_recv(ev.tag, ev.data)
        if pkt:
            core.events.game_data_recv.emit((g, u, pkt))

    # ----- Private Methods -----
    def _setup_game(self, g: ServerGame) -> None:
        core = self.core
        users = core.room.users_of(g)
        gid = core.room.gid_of(g)

        Ag(self, g)['data'] = {
            core.auth.pid_of(u): GameData(gid) for u in users
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
                if Ag(self, g)['fled'].get(p.pid):
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
        pid = core.auth.pid_of(u)
        pkts = Ag(self, g)['data'][pid].get_sent()
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
        core = self.core
        pid = core.auth.pid_of(u)
        return Ag(self, g)['fled'][pid]

    def write(self, g: ServerGame, u: Client, tag: str, data: object) -> None:
        core = self.core
        pid = core.auth.pid_of(u)
        pkt = Ag(self, g)['data'][pid].feed_send(tag, data)
        if Au(self, u)['game'] is g:
            # Only send game data when user in the requested game
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
        core = self.core
        pid = core.auth.pid_of(u)
        return Ag(self, g)['data'][pid]

    def players_of(self, g: ServerGame) -> BatchList[Player]:
        return Ag(self, g)['players']
