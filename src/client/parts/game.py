# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING, TypedDict
import logging

# -- third party --
from gevent import Greenlet

# -- own --
from client.base import ClientGameRunner, ForcedKill, Someone, Theone
from game.base import Game, GameData, GameItem, Player
from utils.events import EventHub
from utils.misc import BatchList
import wire

# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('client.parts.Game')
STOP = EventHub.STOP_PROPAGATION


class GamePartAssocOnGame(TypedDict):
    gid: int
    name: str
    users: List[wire.model.User]
    presence: List[wire.PresenceState]
    params: Dict[str, Any]
    players: BatchList[Player]
    items: Dict[Player, List[GameItem]]
    data: GameData
    observe: bool
    greenlet: Greenlet


class GameDisplayInfo(TypedDict):
    type: str
    n_persons: int
    dispname: str
    logo: str
    desc: str
    params: dict


def A(self: GamePart, v: Game) -> GamePartAssocOnGame:
    return v._[self]


class GamePart(object):
    def __init__(self, core: Core):
        self.core = core
        self.games: Dict[int, Game] = {}

        D = core.events.server_command
        D[wire.RoomUsers]      += self._room_users
        D[wire.GameStarted]    += self._game_started
        D[wire.PlayerPresence] += self._player_presence
        D[wire.GameJoined]     += self._game_joined
        D[wire.SetGameParam]   += self._set_game_param
        D[wire.ObserveStarted] += self._observe_started
        D[wire.GameLeft]       += self._game_left
        D[wire.GameEnded]      += self._game_ended
        D[wire.GameData]       += self._game_data

    # ----- Reactions -----
    def _room_users(self, ev: wire.RoomUsers) -> wire.RoomUsers:
        core = self.core

        g = self.games.get(ev.gid)
        if not g:
            return ev

        A(self, g)['users'] = ev.users
        core.events.room_users.emit((g, ev.users))

        return ev

    def _do_start_game(self, gv: wire.model.GameDetail, me_pid: int) -> None:
        core = self.core
        g = self.games[gv['gid']]
        A(self, g)['users'] = gv['users']
        A(self, g)['params'] = gv['params']
        players = self._build_players(g, A(self, g)['users'], me_pid)
        A(self, g)['players'] = players
        items = self._build_items(g, players, gv['items'])
        A(self, g)['items'] = items
        core.events.game_started.emit(g)
        # Game not actually running now,
        # UI should start it by core.game.start_game(g) manually

    def _game_started(self, ev: wire.GameStarted) -> wire.GameStarted:
        core = self.core
        self._do_start_game(ev.game, core.auth.pid)
        return ev

    def _observe_started(self, ev: wire.ObserveStarted) -> wire.ObserveStarted:
        g = self.games[ev.game['gid']]
        A(self, g)['observe'] = True
        self._do_start_game(ev.game, ev.observee)
        return ev

    def _player_presence(self, ev: wire.PlayerPresence) -> wire.PlayerPresence:
        core = self.core
        g = self.games[ev.gid]
        A(self, g)['presence'] = ev.presence
        pl = A(self, g)['players']
        assert len(ev.presence) == len(pl)
        lst = [(p.pid, pr) for p, pr in zip(pl, ev.presence)]
        core.events.player_presence.emit((g, lst))
        return ev

    def _game_joined(self, ev: wire.GameJoined) -> wire.GameJoined:
        gv = ev.game
        gid = gv['gid']
        g = self._make_game(
            gid,
            gv['type'],
            gv['name'],
            gv['users'],
            gv['params'],
        )
        self.games[gid] = g
        core = self.core
        core.events.game_joined.emit(g)
        return ev

    def _set_game_param(self, ev: wire.SetGameParam) -> wire.SetGameParam:
        core = self.core
        core.events.set_game_param.emit(ev)
        return ev

    def _game_left(self, ev: wire.GameLeft) -> wire.GameLeft:
        g = self.games.get(ev.gid)
        if not g:
            return ev

        self.kill_game(g)

        core = self.core
        core.events.game_left.emit(g)

        return ev

    def _game_ended(self, ev: wire.GameEnded) -> wire.GameEnded:
        g = self.games.get(ev.gid)
        if not g:
            return ev

        log.info('=======GAME ENDED=======')
        core = self.core
        core.events.game_ended.emit(g)

        return ev

    def _game_data(self, ev: wire.GameData) -> wire.GameData:
        g = self.games.get(ev.gid)
        if not g:
            return ev
        A(self, g)['data'].feed_recv(ev.tag, ev.data)
        return ev

    # ----- Private Methods -----
    def _make_game(self, gid: int, mode: str, name: str, users: List[wire.model.User], params: Dict[str, Any]) -> Game:
        from thb import modes
        g = modes[mode]()
        assert isinstance(g, Game)

        assoc: GamePartAssocOnGame = {
            'gid':     gid,
            'name':    name,
            'users':   users,
            'presence': [wire.PresenceState.ONLINE for u in users],
            'params':  params,
            'players': BatchList[Player](),
            'items':   {},
            'data':    GameData(gid),
            'observe': False,
            'greenlet': None,
        }
        g._[self] = assoc

        return g

    def _build_players(self, g: Game, uvl: Sequence[wire.model.User], me_pid: int) -> BatchList[Player]:
        assert me_pid in [uv['pid'] for uv in uvl]

        me = Theone(g, me_pid)

        pl = BatchList[Player]([
            me if uv['pid'] == me_pid else Someone(g, uv['pid'])
            for uv in uvl
        ])
        pl[:0] = [Someone(g, 0) for i, npc in enumerate(g.npc_players)]

        return pl

    def _build_items(self, g: Game, players: Sequence[Player], items: Dict[int, List[str]]) -> Dict[Player, List[GameItem]]:
        m = {p.pid: p for p in players}
        return {
            m[pid]: [GameItem.from_sku(i) for i in skus]
            for pid, skus in items.items()
        }

    # ----- Public Methods -----
    def from_gid(self, gid: int) -> Optional[Game]:
        return self.games.get(gid)

    def is_observe(self, g: Game) -> bool:
        return A(self, g)['observe']

    def start_game(self, g: Game) -> None:
        assert A(self, g)['greenlet'] is None, 'Game already started!'

        core = self.core
        gr = ClientGameRunner(core, g)

        @gr.link_exception
        def crash(gr: Greenlet) -> None:
            core.events.game_crashed.emit(g)

        A(self, g)['greenlet'] = gr
        core.runner.start(gr)
        log.info('----- GAME STARTED: %d -----' % A(self, g)['gid'])

    def write(self, g: Game, tag: str, data: object) -> None:
        core = self.core
        pkt = A(self, g)['data'].feed_send(tag, data)
        gid = A(self, g)['gid']
        core.server.write(wire.GameData(
            gid=gid,
            tag=pkt.tag,
            data=pkt.data,
        ))
        # core.events.game_data_send.emit((g, pkt))

    def kill_game(self, g: Game) -> None:
        if gr := A(self, g)['greenlet']:
            gr.kill(ForcedKill)

    def gid_of(self, g: Game) -> int:
        return A(self, g)['gid']

    def name_of(self, g: Game) -> str:
        return A(self, g)['name']

    def gamedata_of(self, g: Game) -> GameData:
        return A(self, g)['data']

    def items_of(self, g: Game) -> Dict[Player, List[GameItem]]:
        return A(self, g)['items']

    def params_of(self, g: Game) -> dict:
        return A(self, g)['params']

    def players_of(self, g: Game) -> BatchList[Player]:
        return A(self, g)['players']

    def theone_of(self, g: Game) -> Theone:
        for p in A(self, g)['players']:
            if isinstance(p, Theone):
                return p
        else:
            raise Exception("Couldn't find Theone!")

    def is_dropped(self, g: Game, p: Player) -> bool:
        assert isinstance(p, Player), p
        idx = A(self, g)['players'].index(p)
        return A(self, g)['presence'][idx] in (
            wire.PresenceState.DROPPED,
            wire.PresenceState.FLED,
        )
