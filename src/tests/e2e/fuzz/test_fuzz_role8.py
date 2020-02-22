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


class TestFuzzTHBattleRole(object):
    def testFuzzTHBattleRole(self):
        env = Environ()
        t = EventTap()

        # from thb.cards import definition
        # definition.card_definition = [(definition.ExinwanCard, 1, 1)] * 1000

        me = gevent.getcurrent()

        def fail_crash(g):
            e = Exception('GAME CRASH')
            e.__cause__ = g.runner.exception
            gevent.kill(me, e)
            return g

        s = env.server_core()
        cl = BatchList([env.client_core() for _ in range(8)])
        c1r = BatchList(cl[1:])
        c = cl[0]
        names = (
            'Reimu', 'Marisa', 'Youmu', 'Sakuya',
            'Satori', 'Koishi', 'Remilia', 'Flandre',
        )
        for i, name in zip(cl, names):
            i.auth.login(name)
        gevent.idle()
        assert all(cl.auth.uid)
        t.tap_all(cl.events.game_joined)
        c.room.create('Test1', 'THBattleRole', {})
        gevent.idle()
        gid = c.game.gid_of(t[c.events.game_joined])
        c1r.room.join(gid)
        gevent.idle()
        assert [gid] * 8 == [i.game.gid_of(t[i.events.game_joined]) for i in cl]
        t.tap_all(cl.events.game_started)

        s.events.game_crashed += fail_crash
        for i in cl:
            g = t[i.events.game_joined]
            i.events.game_crashed += fail_crash
            g.event_observer = UserInputFuzzingHandler(g)

        cl.room.get_ready()
        gevent.idle()
        assert [gid] * 8 == [i.game.gid_of(t[i.events.game_started]) for i in cl]

        gevent.idle()

        def game_ended(g):
            gevent.kill(me, GameEnded())
            return g

        s.events.game_ended += game_ended

        [i.game.start_game(t[i.events.game_started]) for i in cl]

        try:
            gevent.sleep(60)
            raise Exception('Time limit exceeded!')
        except GameEnded:
            pass
