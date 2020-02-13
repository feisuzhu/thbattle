# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import logging
import gevent

# -- third party --
# -- own --
from .mock import Environ

# -- code --
class TestStart2v2(object):
    def testStart2v2(self, caplog):
        env = Environ()
        s = env.server_core()
        c1 = env.client_core()
        c2 = env.client_core()
        c3 = env.client_core()
        c4 = env.client_core()
        c1.auth.login('Reimu')
        c2.auth.login('Marisa')
        c3.auth.login('Youmu')
        c4.auth.login('Sakuya')
        gevent.sleep(0.01)
        assert c1.auth.uid
        assert c2.auth.uid
        assert c3.auth.uid
        assert c4.auth.uid
