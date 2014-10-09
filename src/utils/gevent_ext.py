# -*- coding: utf-8 -*-

# -- stdlib --
from collections import deque
import traceback

# -- third party --
from gevent.hub import Waiter, _NONE, get_hub

# -- own --
# -- code --


def iwait(objects, timeout=None):
    """Yield objects as they are ready, until all are ready or timeout expired.

    *objects* must be iterable yielding instance implementing wait protocol (rawlink() and unlink()).

    Modified version, fixing https://github.com/surfly/gevent/issues/467
    """
    # QQQ would be nice to support iterable here that can be generated slowly (why?)
    waiter = Waiter()
    waiter_switch = waiter.switch
    queue = deque()

    def switch(value=None):
        queue.append(value)
        waiter_switch(True)

    if timeout is not None:
        timer = get_hub().loop.timer(timeout, priority=-1)
        timer.start(switch, _NONE)
    try:
        count = len(objects)
        for obj in objects:
            obj.rawlink(switch)

        n = count
        while n:
            noti = waiter.get()
            assert noti is True, 'Invalid switch into iwait'
            waiter.clear()
            while queue:
                item = queue.popleft()
                if item is _NONE:
                    return
                yield item
                n -= 1

    finally:
        if timeout is not None:
            timer.stop()
        for obj in objects:
            unlink = getattr(obj, 'unlink', None)
            if unlink:
                try:
                    unlink(switch)
                except:
                    traceback.print_exc()
