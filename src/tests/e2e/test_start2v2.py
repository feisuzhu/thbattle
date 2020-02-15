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

        s = env.server_core()
        c1234 = BatchList([env.client_core() for _ in range(4)])
        c234 = BatchList(c1234[-3:])
        c1, c2, c3, c4 = c1234
        c1.auth.login('Reimu')
        c2.auth.login('Marisa')
        c3.auth.login('Youmu')
        c4.auth.login('Sakuya')
        gevent.idle()
        assert all(c1234.auth.uid)
        t.tap_all(c1234.events.game_joined)
        c1.room.create('Test1', 'THBattle2v2', {})
        gevent.idle()
        gid = c1.game.gid_of(t[c1.events.game_joined])
        c234.room.join(gid)
        gevent.idle()
        assert [gid] * 3 == [c.game.gid_of(t[c.events.game_joined]) for c in c234]
        t.tap_all(c1234.events.game_started)
        c1234.room.get_ready()
        gevent.idle()
        assert [gid] * 4 == [c.game.gid_of(t[c.events.game_started]) for c in c1234]
        gevent.idle()
        [c.game.start_game(t[c.events.game_started]) for c in c1234]
        gevent.idle()
        gevent.sleep(3)
        1/0
