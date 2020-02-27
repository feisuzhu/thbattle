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


def wait():
    gevent.idle()
    gevent.sleep(0.01)
    gevent.idle()


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
        c.auth.login('Reimu')
        wait()
        assert c.auth.uid
        t += c.events.game_joined
        c.room.create('Test1', 'THBattleNewbie', {})
        wait()
        t += c.events.game_started

        s.events.game_crashed += fail_crash

        g = t[c.events.game_joined]
        c.events.game_crashed += fail_crash
        g.event_observer = UserInputFuzzingHandler(g)

        c.room.get_ready()
        wait()

        def game_ended(g):
            gevent.kill(me, GameEnded())
            return g

        s.events.game_ended += game_ended

        c.game.start_game(t[c.events.game_started])

        try:
            gevent.sleep(4)
            raise Exception('Time limit exceeded!')
        except GameEnded:
            pass
