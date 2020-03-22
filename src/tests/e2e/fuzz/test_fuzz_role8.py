# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
import gevent

# -- own --
from ..mock import Environ, EventTap
from utils.misc import BatchList
from .common import UserInputFuzzingHandler, let_it_go
from game.base import sync_primitive
from thb.actions import THBEventHandler
from thb.actions import COMMON_EVENT_HANDLERS


# -- code --
class GameEnded(Exception):
    pass


class ParanoidSyncHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, arg):
        g = self.game
        if hasattr(g, 'players'):
            me = [len(ch.cards) for ch in g.players]
            svr = sync_primitive(me, g.players)
            assert me == svr, (me, svr)
        return arg


class TestFuzzTHBattleRole(object):
    def testFuzzTHBattleRole(self):
        env = Environ()
        t = EventTap()

        # from thb.cards import definition
        # definition.card_definition = [(definition.ExinwanCard, 1, 1)] * 1000

        COMMON_EVENT_HANDLERS.add(ParanoidSyncHandler)

        me = gevent.getcurrent()

        def fail_crash(g):
            e = Exception('GAME CRASH')
            e.__cause__ = g.runner.exception
            gevent.kill(me, e)
            return g

        s = env.server_core()
        cl = BatchList([env.client_core() for _ in range(8)])
        t.tap(s, *cl)

        c1r = BatchList(cl[1:])
        c = cl[0]
        names = (
            'Reimu', 'Marisa', 'Youmu', 'Sakuya',
            'Satori', 'Koishi', 'Remilia', 'Flandre',
        )
        for i, name in zip(cl, names):
            i.auth.login(name)
        gevent.idle(-100)
        assert all(cl.auth.uid)
        c.room.create('Test1', 'THBattleRole', {})
        gevent.idle(-100)
        gid = c.game.gid_of(t[c.events.game_joined])
        c1r.room.join(gid)
        gevent.idle(-100)
        assert [gid] * 8 == [i.game.gid_of(t[i.events.game_joined]) for i in cl]

        s.events.game_crashed += fail_crash
        for i in cl:
            g = t[i.events.game_joined]
            i.events.game_crashed += fail_crash
            g.event_observer = UserInputFuzzingHandler(g)

        cl.room.get_ready()
        gevent.idle(-100)
        assert [gid] * 8 == [i.game.gid_of(t[i.events.game_started]) for i in cl]

        gevent.idle(-100)

        def game_ended(g):
            gevent.kill(me, GameEnded())
            return g

        s.events.game_ended += game_ended

        [i.game.start_game(t[i.events.game_started]) for i in cl]

        try:
            # gevent.sleep(5)
            let_it_go(*cl)
        except GameEnded:
            pass
