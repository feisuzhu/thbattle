# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
import gevent

# -- own --
from .mock import Environ, EventTap


# -- code --
class GameEnded(Exception):
    pass


def wait():
    gevent.idle(-100)
    gevent.sleep(0.01)
    gevent.idle(-100)


class TestMatching(object):
    def testMatching(self):
        env = Environ()
        t = EventTap()

        s = env.server_core()
        a = env.client_core()
        b = env.client_core()
        t.tap(a, b)

        a.auth.login("Alice")
        b.auth.login("Bob")
        wait()

        # Can setup matching
        a.matching.start(['THBattleKOF'])
        a.matching.stop()
        wait()
        b.matching.start(['THBattleKOF'])
        wait()
        assert a.events.game_joined not in t
        assert s.lobby.state_of(s.lobby.get(a.auth.pid)) == 'lobby'
        assert s.lobby.state_of(s.lobby.get(b.auth.pid)) == 'lobby'
        a.matching.start(['THBattleKOF'])
        wait()
        assert a.events.game_joined in t
        assert s.lobby.state_of(s.lobby.get(a.auth.pid)) == 'room'
        assert s.lobby.state_of(s.lobby.get(b.auth.pid)) == 'room'
        a.room.leave()
        wait()
        s.matching._do_gc_stuck_matching()
        assert a.events.game_left in t
        assert s.lobby.state_of(s.lobby.get(a.auth.pid)) == 'lobby'
        assert s.lobby.state_of(s.lobby.get(b.auth.pid)) == 'lobby'
