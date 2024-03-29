# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import logging

# -- third party --
import gevent

# -- own --
from .mock import Environ, EventTap


# -- code --
class GameEnded(Exception):
    pass


log = logging.getLogger('UnitTest')


def wait():
    gevent.idle(-100)
    gevent.sleep(0.01)
    gevent.idle(-100)


class TestContest(object):
    def testContest(self):
        env = Environ()
        t = EventTap()

        s = env.server_core()
        proton = env.client_core()
        a, b, c, d, e = [env.client_core() for _ in range(5)]
        t.tap(proton, a, b, c, d, e)
        proton.auth.login("Proton")
        a.auth.login("Alice")
        b.auth.login("Bob")
        c.auth.login("Cirno")
        e.auth.login("Eirin")
        wait()

        assert proton.auth.pid == 2
        assert a.auth.pid > 0
        assert b.auth.pid > 0
        assert c.auth.pid > 0
        assert e.auth.pid > 0

        # Wrong players count
        proton.contest.setup("TestContest", "THBattle2v2", [a.auth.pid, b.auth.pid]); wait()
        assert t.take(proton.events.server_error) == 'wrong_players_count'
        assert a.events.game_joined not in t
        assert b.events.game_joined not in t

        # Happy path
        # Alice wondering in lobby,
        # Bob fighting with Cirno,
        # Cirno rubberducking Bob fighting Cirno (haha),
        # and Daiyousei not showing at the time.
        b.room.create('Wow', 'THBattleNewbie', {}); wait()
        s.observe.add_bigbrother(c.auth.pid)
        b.room.get_ready()
        c.observe.observe(b.auth.pid); wait()
        assert b.events.game_started in t
        assert c.events.game_started in t
        t.clear()
        proton.contest.setup("TestContest", "THBattleDummy4", [i.auth.pid for i in (a, b, c)] + [s.backend.pid_of('Daiyousei')]); wait()
        assert a.events.game_joined in t
        assert b.events.game_joined not in t
        assert c.events.game_joined in t
        assert d.events.game_joined not in t
        assert e.events.game_joined not in t

        # Daiyousei poped up, should be pulled into contest
        d.auth.login('Daiyousei'); wait()
        gevent.sleep(0.02)
        assert d.events.game_joined in t

        # Bob exits, should be pulled into contest too
        b.room.leave(); wait()
        gevent.sleep(0.02)
        assert b.events.game_joined in t

        # Onlookers should not be able to interfere
        gid = a.game.gid_of(t[a.events.game_joined])
        e.room.join(gid); wait()
        assert t.take(e.events.server_error) == 'not_competitor'

        # Start the contest
        t.clear()
        a.room.get_ready()
        b.room.get_ready()
        c.room.get_ready()
        d.room.get_ready()
        wait()
