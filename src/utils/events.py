# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable, Generic, List, Tuple, TypeVar
import logging
import sys
import zlib

# -- third party --
# -- own --

# -- code --
log = logging.getLogger('utils.events')
T = TypeVar('T')
EventCallback = Callable[[T], T | 'EventHub.StopPropagation']


class WithPriority(Generic[T]):

    def __init__(self, cb: EventCallback, prio: float):
        self._cb = cb
        self._prio = prio


class EventHub(Generic[T]):
    __slots__ = ('_subscribers', 'name')

    class StopPropagation:
        __slots__ = ()

    STOP_PROPAGATION = StopPropagation()

    _subscribers: List[Tuple[float, EventCallback]]

    def __init__(self):
        self._subscribers = []
        self.name: str = '[Anonymous]'

    def subscribe(self, cb: EventCallback, prio: float):
        self._subscribers.append((prio, cb))
        self._subscribers.sort(key=lambda v: v[0])
        return self

    def __iadd__(self, cb: EventCallback | WithPriority):
        if isinstance(cb, WithPriority):
            self.subscribe(cb._cb, cb._prio)
        else:
            # deterministic priority
            f = sys._getframe(1)
            s = '{}:{}'.format(f.f_code.co_filename, f.f_lineno).encode('utf-8')
            prio = zlib.crc32(s) * 1.0 / 0x100000000
            self.subscribe(cb, prio)

        return self

    def emit(self, ev: T):

        if not (self.name.endswith('::client_command') and isinstance(ev, tuple) and ev[1].__class__.__name__ == 'Beat'):
            # Filter out Beat messages to ease debugging
            log.debug('Handling event %s %s', self.name, ev)

        if not self._subscribers:
            # log.debug('Emitting event %s when no subscribers present!', self.name)
            return

        for prio, cb in self._subscribers:
            r = cb(ev)

            if isinstance(r, EventHub.StopPropagation):
                return None
            else:
                ev = r

            if ev is None:
                raise Exception("Returning None in EventHub, last callback: %s", cb)

        return ev


class FSM(object):
    __slots__ = ('_context', '_valid', '_state', '_callback')

    def __init__(self, context, valid, initial, callback):
        if initial not in valid:
            raise Exception('State not in valid choices!')

        self._context  = context
        self._valid    = valid
        self._state    = initial
        self._callback = callback

    def transit(self, state):
        if state not in self._valid:
            raise Exception('Invalid state transition!')

        if state == self._state:
            return

        old, self._state = self._state, state
        self._callback(self._context, old, state)

    def __eq__(self, other):
        return self._state == other

    def __repr__(self):
        return f"FSM:'{self._state}'"

    @property
    def state(self) -> str:
        return self._state

    @staticmethod
    def to_evhub(evhub):
        return lambda ctx, f, t: evhub.emit((ctx, f, t))
