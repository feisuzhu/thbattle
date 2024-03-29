# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
import gevent

# -- own --
from ..mock import Environ, EventTap
from .common import let_it_go
from thb.bot import BotUserInputHandler


# -- code --
class GameEnded(Exception):
    pass


def wait():
    gevent.idle(-100)
    gevent.sleep(0.01)
    gevent.idle(-100)


class TestFuzzTHBattleFaith(object):
    def testFuzzTHBattleFaith(self):
        env = Environ()
        t = EventTap()

        me = gevent.getcurrent()

        def fail_crash(g):
            e = Exception('GAME CRASH')
            e.__cause__ = g.runner.exception
            gevent.kill(me, e)
            return g

        s = env.server_core()
        c = env.client_core()
        t.tap(s, c)

        c.auth.login('Reimu')
        wait()
        assert c.auth.pid
        c.room.create('Test1', 'THBattleNewbie', {})
        wait()

        s.events.game_crashed += fail_crash

        g = t[c.events.game_joined]
        c.events.game_crashed += fail_crash
        g.event_observer = BotUserInputHandler(g)

        c.room.get_ready()
        wait()

        def game_ended(g):
            gevent.kill(me, GameEnded())
            return g

        s.events.game_ended += game_ended

        c.game.start_game(t[c.events.game_started])

        try:
            let_it_go(c)
        except GameEnded:
            pass
