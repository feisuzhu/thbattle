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


class TestRoom(object):
    def testRoom(self):
        env = Environ()
        t = EventTap()

        s = env.server_core()
        a = env.client_core()
        b = env.client_core()
        t.tap(a, b)

        a.auth.login("Alice")
        b.auth.login("Bob")
        wait()

        # Can cancel ready
        a.room.create('Boom', 'THBattle2v2', {})
        a.room.get_ready()
        wait()
        assert a.events.game_joined in t
        assert s.lobby.state_of(s.lobby.get(a.auth.pid)) == 'ready'
        a.room.cancel_ready(); wait()
        assert s.lobby.state_of(s.lobby.get(a.auth.pid)) == 'room'

        # Changing location won't crash
        a.room.change_location(-1)
        a.room.change_location(0)
        a.room.change_location(1)
        a.room.change_location(2)
        a.room.change_location(3)
        a.room.change_location(4)
        a.room.change_location(5)
        wait()
        assert s.lobby.state_of(s.lobby.get(a.auth.pid)) == 'room'

        # Can set param
        gid = a.game.gid_of(t[a.events.game_joined])
        a.room.set_game_param("whatever", "meh")
        a.room.set_game_param("random_force", "foo")
        wait()
        assert s.game.params_of(s.room.get(gid))['random_force'] == True  # noqa
        a.room.set_game_param("random_force", False); wait()
        assert s.game.params_of(s.room.get(gid))['random_force'] == False  # noqa

        # Send room users
        t.clear()
        a.room.get_room_users(); wait()
        assert a.events.room_users in t
        a.room.leave()

        # Can handle crashed game
        t.clear()
        s.runner._paranoid = False
        a.runner._paranoid = False
        a.room.create('meh', 'THBattleCrash', {}); wait()
        gid = a.game.gid_of(t[a.events.game_joined])
        g = s.room.get(gid)
        a.room.get_ready(); wait()
        wait()
        assert s.game.is_crashed(g), g._

    def testPivot(self):
        env = Environ()
        t = EventTap()

        s = env.server_core()
        a = env.client_core()
        b = env.client_core()
        a2 = env.client_core()
        t.tap(a, b, a2)

        a.auth.login("Alice")
        b.auth.login("Bob")
        wait()

        # Should be able to pivot
        a.room.create('Boom', 'THBattleHalt2', {})
        a.room.get_ready()
        wait()
        gid = a.game.gid_of(t[a.events.game_joined])
        b.room.join(gid)
        b.room.get_ready()
        wait()
        a.game.start_game(t[a.events.game_started])
        b.game.start_game(t[b.events.game_started])
        wait()

        a2.auth.login("Alice")
        wait()
        assert a.events.game_left not in t
        assert a2.events.game_left not in t
        assert a2.events.game_joined in t
        assert a2.events.game_started in t
