# -- coding: utf-8 -*-

from gevent.hub import _NONE, Waiter
from gevent import core


def waitany(objects, timeout=None):
    waiter = Waiter()
    switch = waiter.switch

    if not objects:
        return None

    timer = None
    if timeout is not None:
        timer = core.timer(timeout, switch, _NONE)

    try:
        for obj in objects:
            obj.rawlink(switch)

        rst = waiter.get()
        return None if rst is _NONE else rst

    finally:
        timer and timer.cancel()

        for obj in objects:
            unlink = getattr(obj, 'unlink', None)
            if unlink:
                try:
                    unlink(switch)
                except:
                    import traceback
                    traceback.print_exc()
