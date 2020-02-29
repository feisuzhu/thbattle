# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
import gevent

# -- own --
from .mock import Environ, EventTap
from game.base import EventHandler


# -- code --
class GameEnded(Exception):
    pass


def wait():
    gevent.idle()
    gevent.sleep(0.01)
    gevent.idle()


class TestAdmin(object):
    def testKick(self):
        env = Environ()
        t = EventTap()

        _ = env.server_core()
        proton = env.client_core()
        naughty = env.client_core()
        proton.auth.login("Proton")
        naughty.auth.login("Naughty")

        wait()

        assert proton.auth.uid == 2
        assert naughty.auth.uid

        t += proton.events.server_dropped
        t += naughty.events.server_dropped

        naughty.admin.kick(proton.auth.uid)
        wait()

        assert proton.events.server_dropped not in t
        assert naughty.events.server_dropped not in t

        proton.admin.kick(naughty.auth.uid)
        wait()

        assert proton.events.server_dropped not in t
        assert naughty.events.server_dropped in t

    def testKillGame(self):
        env = Environ()
        t = EventTap()

        s = env.server_core()
        proton = env.client_core()
        naughty = env.client_core()
        proton.auth.login("Proton")
        naughty.auth.login("Naughty")

        wait()

        assert proton.auth.uid == 2
        assert naughty.auth.uid

        naughty.admin.kick(proton.auth.uid)

        wait()

        class Halt(EventHandler):
            def handle(self, evt: str, arg):
                gevent.sleep(10000)

        t += naughty.events.game_joined
        naughty.room.create('Boom!', 'THBattleNewbie', {})
        wait()
        g = t[naughty.events.game_joined]
        g.event_observer = Halt(g)
        gid = naughty.game.gid_of(g)
        wait()
        assert s.room.get(gid)
        proton.admin.kill_game(gid)
        wait()
        assert not s.room.get(gid)

    def testSystemCommands(self):
        env = Environ()

        _ = env.server_core()
        proton = env.client_core()
        proton.auth.login("Proton")

        wait()

        proton.admin.clearzombies()
        proton.admin.stacktrace()
        proton.admin.migrate()

        wait()
