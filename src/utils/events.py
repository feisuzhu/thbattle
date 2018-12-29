# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Callable, Generic, List, Tuple, TypeVar, Union
import logging
import sys
import zlib

# -- third party --
# -- own --

# -- code --
log = logging.getLogger('utils.events')
T = TypeVar('T')


class EventHub(Generic[T]):
    __slots__ = ('_subscribers',)

    class StopPropagation:
        __slots__ = ()

    STOP_PROPAGATION = StopPropagation()

    _subscribers: List[Tuple[float, Callable[[T], Union[T, StopPropagation]]]]

    def __init__(self):
        self._subscribers = []

    def subscribe(self, cb: Callable[[T], Union[T, StopPropagation]], prio: float):
        self._subscribers.append((prio, cb))
        self._subscribers.sort(key=lambda v: v[0])
        return self

    def __iadd__(self, cb: Callable[[T], Union[T, StopPropagation]]):
        # deterministic priority
        f = sys._getframe(1)
        s = '{}:{}'.format(f.f_code.co_filename, f.f_lineno).encode('utf-8')
        prio = zlib.crc32(s) * 1.0 / 0x100000000
        self.subscribe(cb, prio)
        return self

    def emit(self, ev: T):
        if not self._subscribers:
            log.warning('Emit event when no subscribers present!')
            return

        for prio, cb in self._subscribers:
            r = cb(ev)

            if isinstance(r, EventHub.StopPropagation):
                return None
            else:
                ev = r

            if ev is None:
                raise Exception("Returning None in EventHub!")

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
        return f'FSM:<{self._state}>'

    @property
    def state(self) -> str:
        return self._state

    @staticmethod
    def to_evhub(evhub):
        return lambda ctx, f, t: evhub.emit((ctx, f, t))
