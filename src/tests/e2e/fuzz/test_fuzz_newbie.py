# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
import gevent

# -- own --
from ..mock import Environ, EventTap
from utils.misc import BatchList
from .user_input import UserInputFuzzingHandler


# -- code --
class GameEnded(Exception):
    pass


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

        g = t[c1.events.game_started]
        g.event_observer = UserInputFuzzingHandler(g)

        def game_ended(g):
            gevent.kill(me, GameEnded())
            return g

        s.events.game_ended += game_ended

        c1.game.start_game(t[c1.events.game_started])

        try:
            gevent.sleep(2)
            raise Exception('Time limit exceeded!')
        except GameEnded:
            pass
