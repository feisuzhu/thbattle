# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
import gevent

# -- own --
from .mock import Environ, EventTap
from utils.misc import BatchList


# -- code --
class TestStart2v2(object):
    def testStart2v2(self):
        env = Environ()
        t = EventTap()

        me = gevent.getcurrent()

        def fail_crash(g):
            e = Exception('GAME CRASH')
            e.__cause__ = g.runner.exception
            gevent.kill(me, e)

        s = env.server_core()
        c1 = env.client_core()
        c1.auth.login('Reimu')
        gevent.idle()
        assert c1.auth.uid
        t += c1.events.game_joined
        c1.room.create('Test1', 'THBattleNewbie', {})
        gevent.idle()
        t += c1.events.game_started
        c1.room.get_ready()
        gevent.idle()
        c1.events.game_crashed += fail_crash
        c1.game.start_game(t[c1.events.game_started])
        gevent.idle()
        gevent.sleep(3)
        1/0

