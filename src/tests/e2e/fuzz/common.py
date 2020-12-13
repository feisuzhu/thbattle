# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import logging

# -- third party --
import gevent

# -- own --

# -- code --
log = logging.getLogger('UserInputFuzzingHandler')


def let_it_go(*cores):
    while True:
        gevent.idle(-100)

        for i in range(10):
            if any(c.server._ep.active for c in cores):
                break

            gevent.sleep(0.05)
        else:
            raise Exception('STUCK!')

        for c in cores:
            c.server._ep.active = False
