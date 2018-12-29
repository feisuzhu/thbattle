# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Callable, Optional, Sequence, Tuple, TypeVar, Union
import functools
import logging

# -- third party --
# -- own --
from server.endpoint import Client
from utils.events import EventHub
from wire.msg import Message


# -- code --
log = logging.getLogger("server.utils")
STOP = EventHub.STOP_PROPAGATION

T = TypeVar('T', bound=Message)


def command(*states: Sequence[str]) -> Callable[[Callable[[Any, Client, T], Optional[EventHub.StopPropagation]]], Callable[[Any, Tuple[Client, T]], Union[Tuple[Client, T], EventHub.StopPropagation]]]:
    def decorate(f: Any) -> Any:
        @functools.wraps(f)
        def wrapper(self: Any, ev: Tuple[Client, T]) -> Union[Tuple[Client, T], EventHub.StopPropagation]:
            core = self.core
            u, msg = ev
            if core.lobby.state_of(u) not in states:
                return ev
            else:
                ret = f(self, u, msg)
                if ret is STOP:
                    return STOP
                return ev

        return wrapper

    return decorate
