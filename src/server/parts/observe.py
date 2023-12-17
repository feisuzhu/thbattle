# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import List, Optional, Set, TYPE_CHECKING, Tuple, TypedDict
import logging

# -- third party --
from gevent import Greenlet

# -- own --
from endpoint import Endpoint
from game.base import Packet
from server.base import Game
from server.endpoint import Client
from server.utils import command
from utils.events import WithPriority
from utils.misc import throttle
import wire

# -- typing --
if TYPE_CHECKING:
    from server.core import Core  # noqa: F401


# -- code --
log = logging.getLogger('Observe')


class ObserveAssocOnClient(TypedDict):
    obs: Set[Client]      # observers
    reqs: Set[int]        # observe requests
    ob: Optional[Client]  # observing


def Au(self: Observe, u: Client) -> ObserveAssocOnClient:
    return u._[self]


class ObserveAssocOnGame(TypedDict):
    _notifier: Optional[Greenlet]


def Ag(self: Observe, g: Game) -> ObserveAssocOnGame:
    return g._[self]


class Observe(object):
    def __init__(self, core: Core):
        self.core = core

        # core.events.user_state_transition += self.handle_ust_observee
        core.events.user_state_transition += WithPriority(self.handle_ust_observee, -1)
        core.events.game_created += self.handle_game_created
        core.events.game_joined += self.handle_game_joined
        core.events.client_dropped += self.handle_client_dropped
        core.events.game_data_send += self.handle_game_data_send

        _ = core.events.client_command
        _[wire.Observe] += self._observe
        _[wire.GrantObserve] += self._grant
        _[wire.LeaveRoom] += self._leave
        _[wire.KickObserver] += self._kick

        self._bigbrothers: List[int] = []

    def __repr__(self) -> str:
        return self.__class__.__name__

    def handle_ust_observee(self, ev: Tuple[Client, str, str]) -> Tuple[Client, str, str]:
        c, f, t = ev

        if (f, t) == ('ready', 'game'):
            for u in Au(self, c)['obs']:
                self._observe_start(u, c)

        elif f in ('room', 'ready', 'game', 'wait') and t == 'lobby':
            core = self.core
            for u in list(Au(self, c)['obs']):
                self.observe_detach(u)

        elif (f, t) == ('game', 'finishing'):
            for u in list(Au(self, c)['obs']):
                self._observe_end(u, c)

        if (f, t) in (('uninitialized', 'freeslot'), ('authed', 'lobby')):
            assoc: ObserveAssocOnClient = {
                'obs': set(),
                'reqs': set(),
                'ob': None,
            }
            c._[self] = assoc

        if f in ('room', 'ready', 'game') or \
           t in ('room', 'ready', 'game'):
            core = self.core
            # TODO: order with core.game?
            g = core.game.current(c)
            if g: self._notify(g)

        return ev

    def handle_client_dropped(self, c: Client) -> Client:
        core = self.core
        if core.lobby.state_of(c) == 'connected':
            return c

        for u in list(Au(self, c)['obs']):
            self.observe_detach(u)

        return c

    def handle_game_created(self, g: Game) -> Game:
        assoc: ObserveAssocOnGame = {
            '_notifier': None
        }
        g._[self] = assoc
        return g

    def handle_game_joined(self, ev: Tuple[Game, Client]) -> Tuple[Game, Client]:
        g, c = ev
        core = self.core
        for ob in Au(self, c)['obs']:
            ob.write(wire.GameJoined(core.view.GameDetail(g)))
            core.lobby.state_of(ob).transit('ob')

        return ev

    def handle_game_data_send(self, ev: Tuple[Game, Client, Packet]) -> Tuple[Game, Client, Packet]:
        core = self.core
        g, u, pkt = ev
        gid = core.room.gid_of(g)
        assert pkt is not None

        obs = Au(self, u)['obs']

        if not obs:
            return ev

        d = Endpoint.encode(wire.GameData(
            gid=gid, tag=pkt.tag, data=pkt.data
        ))

        for u in obs:
            u.raw_write(d)

        return ev

    # ----- Client Commands -----
    @command('lobby')
    def _observe(self, u: Client, ev: wire.Observe) -> None:
        core = self.core

        observee = core.lobby.get(ev.pid)
        if observee is None:
            return

        if core.lobby.state_of(observee) == 'ob':
            observee = Au(self, observee)['ob']
            assert observee

        if core.lobby.state_of(observee) not in ('game', 'room', 'ready'):
            return

        pid = core.auth.pid_of(u)

        if pid in self._bigbrothers:
            observee.write(wire.SystemMsg(
                '管理员对你使用了强制观战，效果拔群。'
                '强制观战功能仅用来处理纠纷，如果涉及滥用，请向 Proton 投诉。'
            ))
            self.observe_attach(u, observee)
            return

        if pid in Au(self, observee)['reqs']:
            # request already sent
            return

        Au(self, observee)['reqs'].add(pid)
        observee.write(wire.ObserveRequest(pid=pid))

    @command('room', 'ready', 'game')
    def _grant(self, c: Client, ev: wire.GrantObserve) -> None:
        if ev.pid not in Au(self, c)['reqs']:
            return

        Au(self, c)['reqs'].remove(ev.pid)

        core = self.core
        ob = core.lobby.get(ev.pid)

        if ob is None:
            return

        if core.lobby.state_of(ob) != 'lobby':
            return

        if ev.grant:
            self.observe_attach(ob, c)
        else:
            ob.write(wire.Error('observe_refused'))

    @command('room', 'ready', 'game')
    def _kick(self, c: Client, ev: wire.KickObserver) -> None:
        core = self.core
        ob = core.lobby.get(ev.pid)
        if not ob:
            return

        g = core.game.current(c)
        if not g: return

        for u in core.room.online_users_of(g):
            if ob in Au(self, u)['obs']:
                break
        else:
            return

        assert core.lobby.state_of(ob) == 'ob', (ob, core.lobby.state_of(ob))

        self.observe_detach(ob)

        # TODO
        '''
        bl = self.ob_banlist[other]
        bl.add(c)

        s = Client.encode(['ob_kick_request', [user, other, len(bl)]])
        for cl in self.users:
            cl.raw_write(s)
            cl.observers and cl.observers.raw_write(s)

        return len(bl) >= len(self.users) // 2

        self.exit_game(other)
        '''

    @command('ob')
    def _leave(self, u: Client, ev: wire.LeaveRoom) -> None:
        self.observe_detach(u)

    # ----- Public Methods -----
    def add_bigbrother(self, pid: int) -> None:
        self._bigbrothers.append(pid)

    def remove_bigbrother(self, pid: int) -> None:
        try:
            self._bigbrothers.remove(pid)
        except Exception:
            pass

    def observe_attach(self, ob: Client, observee: Client) -> None:
        core = self.core

        g = core.game.current(observee)
        if not g:
            return

        users = core.room.online_users_of(g)

        assert observee in users
        assert core.lobby.state_of(ob) == 'lobby'
        assert core.lobby.state_of(observee) in ('room', 'ready', 'game')

        log.info("observe attach")

        Au(self, observee)['obs'].add(ob)
        Au(self, ob)['ob'] = observee
        core.lobby.state_of(ob).transit('ob')

        ob.write(wire.GameJoined(core.view.GameDetail(g)))

        @core.runner.spawn
        def notify_observer() -> None:
            d = Endpoint.encode(wire.ObserverEnter(
                observer=core.auth.pid_of(ob),
                observee=core.auth.pid_of(observee),
            ))

            for u in users:
                u.raw_write(d)
                for i in Au(self, u)['obs']:
                    i.raw_write(d)

        if core.room.is_started(g):
            self._observe_start(ob, observee)
            core.game.replay(observee, to=ob)

    def observe_detach(self, ob: Client) -> None:
        core = self.core
        assert core.lobby.state_of(ob) == 'ob'

        observee = Au(self, ob)['ob']
        if not observee:
            return

        Au(self, ob)['ob'] = None
        Au(self, observee)['obs'].remove(ob)

        # TODO add these back
        # try:
        #     del self.ob_banlist[user]
        # except KeyError:
        #     pass

        core.lobby.state_of(ob).transit('lobby')
        g = core.game.current(observee)

        if not g:
            return

        gid = core.room.gid_of(g)
        ob.write(wire.GameLeft(gid))

        @core.runner.spawn
        def notify_observer_leave() -> None:
            assert observee
            g = core.game.current(observee)
            if not g:
                return

            ul = core.room.online_users_of(g)

            d = Endpoint.encode(wire.ObserverLeave(
                observer=core.auth.pid_of(ob),
                observee=core.auth.pid_of(observee),
            ))

            for u in ul:
                u.raw_write(d)
                for i in Au(self, u)['obs']:
                    i.raw_write(d)

    # ----- Methods -----
    def _observe_start(self, ob: Client, observee: Client) -> None:
        core = self.core
        pid = core.auth.pid_of(observee)
        g = core.game.current(observee)
        assert g

        ob.write(wire.ObserveStarted(core.view.GameDetail(g), observee=pid))
        core.lobby.state_of(ob).transit('ob')

    def _observe_end(self, ob: Client, observee: Client) -> None:
        core = self.core
        g = core.game.current(observee)
        if not g: return
        gid = core.room.gid_of(g)
        ob.write(wire.GameEnded(gid))
        core.lobby.state_of(ob).transit('lobby')

    def _notify(self, g: Game) -> None:
        notifier = Ag(self, g)['_notifier']
        core = self.core

        if notifier:
            notifier()
            return

        @throttle(0.5)
        def _notifier() -> None:
            pl = core.room.users_of(g)
            obs: List[Client] = []
            for u in pl:
                obs.extend(Au(self, u)['obs'])

            core.runner.spawn(core.room.send_room_users, g, obs)

        Ag(self, g)['_notifier'] = _notifier

        _notifier()
