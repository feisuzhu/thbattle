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


class TestInvite(object):
    def testInvite(self):
        env = Environ()
        t = EventTap()

        s = env.server_core()
        a, b, c, d, e = [env.client_core() for _ in range(5)]
        t.tap(a, b, c, d, e)

        a.auth.login("Alice")
        b.auth.login("Bob")
        c.auth.login("Cirno")
        d.auth.login("Daiyousei")
        e.auth.login("Eirin")
        wait()

        assert a.auth.uid > 0
        assert b.auth.uid > 0
        assert c.auth.uid > 0
        assert d.auth.uid > 0
        assert e.auth.uid > 0

        # Onlookers should not be able to join invite only rooms
        a.room.create("TestInvite", "THBattleDummy4", {'invite': True}); wait()
        gid = a.game.gid_of(t.take(a.events.game_joined))
        b.room.join(gid); wait()
        assert t.take(b.events.server_error) == 'not_invited'
        assert b.events.game_joined not in t

        # Happy path
        [a.room.invite(i.auth.uid) for i in (b, c, d)]; wait()
        [i.room.join(gid) for i in (b, c, d)]; wait()
        assert b.events.game_joined in t
        assert c.events.game_joined in t
        assert d.events.game_joined in t

        # Kick happy path
        t.clear()
        a.room.kick(d.auth.uid); wait()
        assert d.events.game_left not in t
        b.room.kick(d.auth.uid); wait()
        assert d.events.game_left in t

        # Banned player can't join again
        t.clear()
        d.room.join(gid); wait()
        assert t.take(d.events.server_error) == 'banned'

        # Ban votes fades away with player left game
        t.clear()
        b.room.leave(); wait()
        d.room.join(gid); wait()
        assert t.take(d.events.server_error) == 'not_invited'
        c.room.invite(d.auth.uid); wait()
        d.room.join(gid); wait()
        assert d.events.game_joined in t
