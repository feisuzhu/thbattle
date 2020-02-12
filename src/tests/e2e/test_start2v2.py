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
        sc = env.server_core()
        cc1 = env.client_core()
        cc2 = env.client_core()
        cc1.auth.login('1111')
        cc2.auth.login('2222')
        gevent.sleep(0.1)
        1/0
