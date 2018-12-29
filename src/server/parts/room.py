# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple
import logging
import time

# -- third party --
from gevent import Greenlet
from mypy_extensions import TypedDict
import gevent

# -- own --
from endpoint import Endpoint
from server.base import Game
from server.endpoint import Client
from server.utils import command
from utils.misc import BatchList, throttle
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Room')


class RoomAssocOnGame(TypedDict):
    gid: int
    users: BatchList[Client]
    left: Dict[Client, bool]
    name: str
    flags: Dict[str, Any]
    start_time: float
    greenlet: Optional[Greenlet]

    _notifier: Optional[Greenlet]


def Ag(self: Room, g: Game) -> RoomAssocOnGame:
    return g._[self]


class Room(object):

    def __init__(self, core: Core):
        self.core = core

        core.events.user_state_transition += self.handle_user_state_transition
        core.events.game_started += self.handle_game_started
        core.events.game_joined += self.handle_game_joined
        core.events.game_left += self.handle_game_left
        core.events.game_ended += self.handle_game_ended
        core.events.core_initialized += self.handle_core_initialized

        D = core.events.client_command
        D[wire.CreateRoom]     += self._create
        D[wire.JoinRoom]       += self._join
        D[wire.LeaveRoom]      += self._leave
        D[wire.GetRoomUsers]   += self._users
        D[wire.GetReady]       += self._get_ready
        D[wire.ChangeLocation] += self._change_location
        D[wire.CancelReady]    += self._cancel_ready

        self.games: Dict[int, Game] = {}

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_core_initialized(self, core: Core) -> Core:
        self._init_freeslot()
        return core

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        c, f, t = ev
        core = self.core

        if t == 'dropped' and f in ('room', 'ready', 'game'):
            self.exit_game(c)

        if f in ('room', 'ready', 'game') or \
           t in ('room', 'ready', 'game'):
            # TODO: order with core.game?
            g = core.game.current(c)
            if g: self._notify(g)

        users = core.lobby.all_users()
        ul = [u for u in users if core.lobby.state_of(u) == 'lobby']
        self._notify_gamelist(ul)

        return ev

    def handle_game_joined(self, ev: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, c = ev
        Ag(self, g)['left'][c] = False
        return ev

    def handle_game_left(self, ev: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, c = ev
        Ag(self, g)['left'][c] = self.is_started(g)
        return ev

    def handle_game_started(self, g: Game) -> Game:
        core = self.core
        users = Ag(self, g)['users']
        assert None not in users

        for u in users:
            assert core.lobby.state_of(u) == 'ready'

        for u in users:
            core.lobby.state_of(u).transit('game')

        Ag(self, g)['start_time'] = time.time()
        return g

    def handle_game_ended(self, g: Game) -> Game:
        core = self.core
        self.games.pop(Ag(self, g)['gid'], 0)

        online_users = self.online_users_of(g)
        if not online_users:
            return g

        old = g

        g = self.create_game(
            old.__class__,
            Ag(self, old)['name'],
            Ag(self, old)['flags'],
        )

        for u in online_users:
            core.lobby.state_of(u).transit('lobby')

        core.events.game_successive_create.emit((old, g))

        for u in Ag(self, old)['users']:
            if self.is_online(old, u):
                self.join_game(g, u)

        return old

    # ----- Client Commands -----
    @command('lobby')
    def _create(self, u: Client, ev: wire.CreateRoom) -> None:
        core = self.core
        from thb import modes

        if ev.mode not in modes:
            return

        g = self.create_game(modes[ev.mode], ev.name, ev.flags)
        core.invite.add_invited(g, u)
        self.join_game(g, u, 0)

    @command('lobby', 'ob')
    def _join(self, u: Client, ev: wire.JoinRoom) -> None:
        g = self.games.get(ev.gid)
        if not g:
            return

        log.info("join game")
        self.join_game(g, u, ev.slot)

    @command('room', 'ready', 'game')
    def _leave(self, u: Client, ev: wire.LeaveRoom) -> None:
        self.exit_game(u)

    @command('lobby')
    def _users(self, u: Client, ev: wire.GetRoomUsers) -> None:
        g = self.games.get(ev.gid)
        if not g:
            return

        self.send_room_users(g, [u])

    @command('room')
    def _get_ready(self, u: Client, ev: wire.GetReady) -> None:
        self.get_ready(u)

    @command('ready')
    def _cancel_ready(self, u: Client, ev: wire.CancelReady) -> None:
        self.cancel_ready(u)

    @command('room', 'ob')
    def _change_location(self, u: Client, ev: wire.ChangeLocation) -> None:
        core = self.core

        if core.lobby.state_of(u) not in ('room', ):
            return

        core = self.core

        g = core.game.current(u)

        if not g:
            raise Exception('change_location called when not in game')

        users = Ag(self, g)['users']

        if (not 0 <= ev.loc < len(users)) or (users[ev.loc] is not self.FREESLOT):
            return

        i = users.index(u)
        users[ev.loc], users[i] = users[i], users[ev.loc]

        # core.events.game_change_location.emit(g)

    # ----- Public Methods -----
    def get_ready(self, u: Client) -> None:
        core = self.core
        g = core.game.current(u)
        if not g:
            log.error('Client attempted to get ready when has no game attached: %s[%s]', u, u._)
            return

        users = Ag(self, g)['users']
        if u not in users:
            raise Exception('WTF')

        core.lobby.state_of(u).transit('ready')

        if all(core.lobby.state_of(u) == 'ready' for u in users):
            # prevent double starting
            if not Ag(self, g)['greenlet']:
                log.info("game starting")
                Ag(self, g)['greenlet'] = gevent.spawn(g.run)

    def is_online(self, g: Game, c: Client) -> bool:
        rst = c is not self.FREESLOT
        rst = rst and c in Ag(self, g)['users']
        rst = rst and not Ag(self, g)['left'][c]
        return bool(rst)

    def is_left(self, g: Game, c: Client) -> bool:
        return Ag(self, g)['left'][c]

    def online_users_of(self, g: Game) -> BatchList[Client]:
        return BatchList([u for u in Ag(self, g)['users'] if self.is_online(g, u)])

    def users_of(self, g: Game) -> BatchList[Client]:
        return Ag(self, g)['users']

    def gid_of(self, g: Game) -> int:
        return Ag(self, g)['gid']

    def name_of(self, g: Game) -> str:
        return Ag(self, g)['name']

    def flags_of(self, g: Game) -> Dict[str, Any]:
        return Ag(self, g)['flags']

    def start_time_of(self, g: Game) -> int:
        return int(Ag(self, g)['start_time'])

    def greenlet_of(self, g: Game) -> Optional[Greenlet]:
        return Ag(self, g)['greenlet']

    def is_started(self, g: Game) -> bool:
        return bool(Ag(self, g)['greenlet'])

    def create_game(self, gamecls: type, name: str, flags: dict) -> Game:
        core = self.core
        gid = self._new_gid()
        g = core.game.create_game(gamecls)
        self.games[gid] = g

        assoc: RoomAssocOnGame = {
            'gid': gid,
            'users': BatchList([self.FREESLOT] * g.n_persons),
            'left': defaultdict(bool),
            'name': name,
            'flags': flags,  # {'match': 1, 'invite': 1}
            'start_time': 0,
            'greenlet': None,

            '_notifier': None,
        }
        g._[self] = assoc

        ev = core.events.game_created.emit(g)
        assert ev
        return g

    def join_game(self, g: Game, u: Client, slot: Optional[int] = None) -> None:
        core = self.core

        assert core.lobby.state_of(u) == 'lobby', core.lobby.state_of(u)

        slot = slot if slot is not None else self._next_slot(g)

        if slot is None:
            return

        if not (0 <= slot < g.n_persons and Ag(self, g)['users'][slot] is self.FREESLOT):
            return

        Ag(self, g)['users'][slot] = u

        core.lobby.state_of(u).transit('room')
        u.write(wire.GameJoined(core.view.GameDetail(g)))

        core.events.game_joined.emit((g, u))

    def exit_game(self, u: Client) -> None:
        core = self.core

        g = core.game.current(u)
        if not g:
            return

        if not self.is_started(g):
            rst = Ag(self, g)['users'].replace(u, self.FREESLOT)
            assert rst

        gid = Ag(self, g)['gid']

        u.write(wire.GameLeft(Ag(self, g)['gid']))

        log.info(
            'Player %s left game [%s]',
            core.auth.name_of(u),
            gid,
        )

        core.lobby.state_of(u).transit('lobby')
        core.events.game_left.emit((g, u))

        if gid not in self.games:
            return

        users = self.online_users_of(g)

        if users:
            return

        if self.is_started(g):
            log.info('Game [%s] aborted', gid)
            core.game.abort(g)
        else:
            log.info('Game [%s] cancelled', gid)
            self.games.pop(gid, 0)

    def send_room_users(self, g: Game, to: List[Client]) -> None:
        core = self.core
        gid = Ag(self, g)['gid']
        pl = [core.view.User(u) for u in Ag(self, g)['users']]
        s = Endpoint.encode(wire.RoomUsers(gid=gid, users=pl))  # former `gameinfo` and `player_change`
        for u in to:
            u.raw_write(s)

    def cancel_ready(self, u: Client) -> None:
        core = self.core
        if core.lobby.state_of(u) != 'ready':
            return

        g = core.game.current(u)
        users = Ag(self, g)['users']
        if u not in users:
            log.error('User not in player list')
            return

        core.lobby.state_of(u).transit('room')

    def get(self, gid: int) -> Optional[Game]:
        return self.games.get(gid)

    # ----- Methods -----
    def _init_freeslot(self) -> None:
        core = self.core
        self.FREESLOT = u = Client(core, None)
        core.auth.set_auth(u, uid=0, name='空位置')
        core.lobby.init_freeslot(u)
        core.lobby.state_of(u).transit('freeslot')

    def _notify(self, g: Game) -> None:
        notifier = Ag(self, g)['_notifier']

        if notifier:
            notifier()
            return

        @throttle(0.5)
        def _notifier() -> None:
            gevent.spawn(self.send_room_users, g, Ag(self, g)['users'])

        Ag(self, g)['_notifier'] = _notifier
        _notifier()

    @throttle(3)
    def _notify_gamelist(self, ul: List[Client]) -> None:
        core = self.core

        lst = [core.view.Game(g) for g in self.games.values()]
        d = Endpoint.encode_bulk([wire.CurrentGames(lst)])

        @gevent.spawn
        def do_send() -> None:
            for u in ul:
                u.raw_write(d)

    def _next_slot(self, g: Game) -> Optional[int]:
        try:
            return Ag(self, g)['users'].index(self.FREESLOT)
        except ValueError:
            return None

    def _new_gid(self) -> int:
        core = self.core
        gid = core.backend.query('query { gameId }')['gameId']
        return gid
