# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Callable, List, TYPE_CHECKING, Tuple
import random
import sys
import typing

# -- third party --
from gevent.event import Event
from mypy_extensions import TypedDict
from typing_extensions import Literal
import gevent
import gevent.hub

# -- own --
from client.base import Game
from game.base import EventHandler


# -- typing --
if TYPE_CHECKING:
    from client.core import Core  # noqa: F401


# -- code --
class GameEvent(TypedDict):
    t: Literal['g']
    g: Game
    evt: str
    arg: Any


class InputEvent(TypedDict):
    t: Literal['i']
    g: Game
    arg: Any
    done: Callable


class SystemEvent(TypedDict):
    t: Literal['s']
    evt: str
    arg: Tuple


class UnityUIEventHook(EventHandler):
    game: Game

    def __init__(self, g: Game):
        EventHandler.__init__(self, g)
        self.game = g
        self.live = False

    def evt_user_input(self, arg: Any) -> None:
        evt = Event()
        g = self.game
        core = g.core
        core.warpgate.feed_ev({'t': 'i', 'g': g, 'arg': arg, 'done': evt.set})
        evt.wait()

    def handle(self, evt: str, arg: Any) -> Any:
        if not self.live and evt not in ('game_begin', 'switch_character', 'reseat'):
            return arg

        g = self.game
        core = g.core

        if evt == 'user_input':
            self.evt_user_input(arg)
        elif evt == '__game_live':
            self.live = True
            return None
        else:
            core.warpgate.feed_ev({'t': 'g', 'g': g, 'evt': evt, 'arg': arg})

        if random.random() < 0.01:
            gevent.sleep(0.005)

        return arg

    def set_live(self) -> None:
        self.live = True
        core = self.game.core
        core.warpgate.feed_ev({'t': 'g', 'g': self.game, 'evt': 'game_live', 'arg': None})


sys.argv = []



class ExecutiveWrapper(object):
    def connect_server(self, host, port):
        from UnityEngine import Debug
        Debug.Log(repr((host, port)))

        @gevent.spawn
        def do():
            Q = self.warpgate.queue_system_event
            Q('connect', self.executive.connect_server((host, port), Q))

    def start_replay(self, rep):
        self.executive.start_replay(rep, self.warpgate.queue_system_event)

    def ignite(self, g):
        g.event_observer = UnityUIEventHook(self.warpgate, g)

        @gevent.spawn
        def start():
            gevent.sleep(0.3)
            svr = g.me.server
            if svr.gamedata_piled():
                g.start()
                svr.wait_till_live()
                gevent.sleep(0.1)
                svr.wait_till_live()
                g.event_observer.set_live()
            else:
                g.event_observer.set_live()
                g.start()


class Warpgate(object):
    def __init__(self, core: Core):
        self.core = core
        self.events: List[Any] = []

        core.events.core_initialized += self.init_warpgate

    def init_warpgate(self, core: Core) -> Core:
        for name, hub in core.events.__dict__.items():
            if name in ('core_initialized', 'server_command'):
                continue

            hub += self.forward_event(name)

        return core

    def forward_event(self, evt: str) -> Callable:
        def forwarder(arg: Any) -> Any:
            self.feed_ev({'t': 's', 'evt': evt, 'arg': arg})
            return arg
        return forwarder

    @typing.overload
    def feed_ev(self, ev: GameEvent) -> None: ...

    @typing.overload
    def feed_ev(self, ev: InputEvent) -> None: ...

    @typing.overload
    def feed_ev(self, ev: SystemEvent) -> None: ...

    def feed_ev(self, ev: Any) -> None:
        self.events.append(ev)

    def get_events(self) -> List[Any]:
        l = self.events
        self.events = []
        return l
