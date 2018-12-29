# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import List, Optional, Sequence, TYPE_CHECKING, Tuple
import logging

# -- third party --
from mypy_extensions import TypedDict
import gevent

# -- own --
from server.base import Game, HumanPlayer
from server.endpoint import Client
from server.utils import command
from utils.events import EventHub
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Match')


class MatchAssocOnGame(TypedDict):
    uids: List[int]


def A(self: Match, g: Game) -> MatchAssocOnGame:
    return g._[self]


class Match(object):
    def __init__(self, core: Core):
        self.core = core

        core.events.user_state_transition += self.handle_user_state_transition
        core.events.game_started += self.handle_game_started
        core.events.game_aborted += self.handle_game_aborted
        core.events.game_ended += self.handle_game_ended
        core.events.game_successive_create += self.handle_game_successive_create

        D = core.events.client_command
        D[wire.SetupMatch] += self._match
        D[wire.JoinRoom].subscribe(self._room_join_match_limit, -3)

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_user_state_transition(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        c, f, t = ev
        return ev

    def handle_game_started(self, g: Game) -> Game:
        core = self.core

        name = core.room.name_of(g)
        flags = core.room.flags_of(g)
        users = core.room.users_of(g)

        if flags.get('match'):
            core.connect.speaker(
                '文文', '“%s”开始了！参与玩家：%s' % (
                    name, '，'.join([core.auth.name_of(u) for u in users])
                )
            )

        return g

    def handle_game_aborted(self, g: Game) -> Game:
        core = self.core
        if core.room.is_started(g) and core.room.flags_of(g).get('match'):
            core.connect.speaker(
                '文文', '“%s”意外终止了，比赛结果作废！' % core.room.name_of(g)
            )

        return g

    def handle_game_ended(self, g: Game) -> Game:
        core = self.core

        if not core.room.flags_of(g).get('match'):
            return g

        if core.game.is_aborted(g):
            return g

        winners: List[Client] = [
            u.client for u in core.game.winners_of(g)
            if isinstance(u, HumanPlayer)
        ]

        core.connect.speaker(
            '文文',
            '“%s”结束了！获胜玩家：%s' % (
                core.room.name_of(g),
                '，'.join([core.auth.name_of(u) for u in winners])
            )
        )

        return g

    def handle_game_successive_create(self, ev: Tuple[Game, Game]) -> Tuple[Game, Game]:
        core = self.core
        old, g = ev
        flags = core.room.flags_of(g)
        if flags.get('match'):
            fields = old._[self]
            g._[self] = fields
            self._start_poll(g, fields['uids'])
        return ev

    # ----- Client Commands -----
    @command()
    def _match(self, c: Client, ev: wire.SetupMatch) -> None:
        core = self.core
        from thb import modes
        gamecls = modes[ev.mode]
        if len(ev.uids) != gamecls.n_persons:
            c.write(wire.SystemMsg('参赛人数不正确'))
            return

        g = core.room.create_game(gamecls, ev.name, {'match': True})

        assoc: MatchAssocOnGame = {
            'uids': ev.uids,
        }
        g._[self] = assoc
        self._start_poll(g, ev.uids)

    @command()
    def _room_join_match_limit(self, u: Client, ev: wire.JoinRoom) -> Optional[EventHub.StopPropagation]:
        core = self.core

        g = core.room.get(ev.gid)
        if not g:
            return None

        flags = core.room.flags_of(g)
        uid = core.auth.uid_of(u)

        if flags.get('match'):
            uid = core.auth.uid_of(u)
            if uid not in A(self, g)['uids']:
                u.write(wire.Error('not_invited'))
                return EventHub.STOP_PROPAGATION

        return None

    # ----- Methods -----
    def _start_poll(self, g: Game, uids: Sequence[int]) -> None:
        core = self.core
        gid = core.room.gid_of(g)
        name = core.room.name_of(g)

        @gevent.spawn
        def _noti() -> None:
            gevent.sleep(1),
            core.connect.speaker('文文', '“%s”房间已经建立，请相关玩家就位！' % name)

        @gevent.spawn
        def pull() -> None:
            while core.room.get(gid) is g:
                users = core.room.online_users_of(g)
                uids = {core.auth.uid_of(u) for u in users}
                match_uids = set(A(self, g)['uids'])

                for uid in match_uids - uids:
                    u = core.lobby.get(uid)
                    if not u:
                        continue

                    if core.lobby.state_of(u) == 'lobby':
                        core.room.join_game(g, u)
                    elif core.lobby.state_of(u) in ('ob', 'ready', 'room'):
                        core.room.exit_game(u)
                        gevent.sleep(1)
                        core.room.join_game(g, u)
                    elif core.lobby.state_of(u) == 'game':
                        gevent.spawn(u.write, wire.SystemMsg('你有比赛房间，请尽快结束游戏参与比赛'))

                    gevent.sleep(0.1)

                gevent.sleep(30)
