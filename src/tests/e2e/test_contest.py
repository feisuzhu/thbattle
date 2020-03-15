# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import logging

# -- third party --
import gevent

# -- own --
from .mock import Environ, EventTap
from game.base import EventHandler


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
        proton.auth.login("Proton")
        a.auth.login("Alice")
        b.auth.login("Bob")
        c.auth.login("Cirno")
        e.auth.login("Eirin")
        wait()

        assert proton.auth.uid == 2
        assert a.auth.uid > 0
        assert b.auth.uid > 0
        assert c.auth.uid > 0
        assert e.auth.uid > 0

        t += proton.events.server_error
        t += a.events.game_joined
        t += b.events.game_joined
        t += c.events.game_joined
        t += d.events.game_joined
        t += e.events.game_joined
        t += a.events.game_started
        t += b.events.game_started
        t += c.events.game_started
        t += d.events.game_started
        t += e.events.game_started

        # Wrong players count
        proton.contest.setup("TestContest", "THBattle2v2", [a.auth.uid, b.auth.uid]); wait()
        assert t.take(proton.events.server_error) == 'wrong_players_count'
        assert a.events.game_joined not in t
        assert b.events.game_joined not in t

        # Happy path
        # Alice wondering in lobby,
        # Bob fighting with Cirno,
        # Cirno rubberducking Bob fighting Cirno (haha),
        # and Daiyousei not showing at the time.
        b.room.create('Wow', 'THBattleNewbie', {}); wait()
        s.observe.add_bigbrother(c.auth.uid)
        b.room.get_ready()
        c.observe.observe(b.auth.uid); wait()
        assert b.events.game_started in t
        assert c.events.game_started in t
        t.clear()
        proton.contest.setup("TestContest", "THBattleDummy4", [i.auth.uid for i in (a, b, c)] + [s.backend.uid_of('Daiyousei')]); wait()
        assert a.events.game_joined in t
        assert b.events.game_joined not in t
        assert c.events.game_joined in t
        assert d.events.game_joined not in t
        assert e.events.game_joined not in t

        # Daiyousei poped up, should be pulled into contest
        d.auth.login('Daiyousei'); wait()
        gevent.sleep(0.2)
        assert d.events.game_joined in t

        # Bob exits, should be pulled into contest too
        b.room.leave(); wait()
        gevent.sleep(0.2)
        assert b.events.game_joined in t

        # Onlookers should not be able to interfere
        t += e.events.server_error
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
        gevent.sleep(0.2)
