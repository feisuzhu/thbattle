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


class TestObserve(object):
    def testObserve(self):
        env = Environ()
        t = EventTap()

        s = env.server_core()
        youmu = env.client_core()
        yuyuko = env.client_core()
        youmu.auth.login("Youmu")
        yuyuko.auth.login("Yuyuko")
        wait()
        assert youmu.auth.uid
        assert yuyuko.auth.uid

        t += youmu.events.game_joined
        t += yuyuko.events.game_joined
        t += youmu.events.game_started
        t += yuyuko.events.game_started
        t += youmu.events.game_left
        t += yuyuko.events.game_left
        t += youmu.events.game_ended
        t += yuyuko.events.game_ended
        t += youmu.events.observe_request
        t += yuyuko.events.observe_request

        youmu.room.create('Boom', 'THBattleDummy1', {}); wait()
        assert youmu.events.game_joined in t

        # Grant without request
        youmu.observe.grant(yuyuko.auth.uid, True); wait()
        assert yuyuko.events.game_joined not in t

        # Denied request
        yuyuko.observe.observe(youmu.auth.uid); wait()
        assert t.take(youmu.events.observe_request) == yuyuko.auth.uid
        youmu.observe.grant(yuyuko.auth.uid, False); wait()
        assert yuyuko.events.game_joined not in t

        # Subsequent grant should not take effect
        youmu.observe.grant(yuyuko.auth.uid, True); wait()
        assert yuyuko.events.game_joined not in t

        # Subsequent request should not take effect
        yuyuko.observe.observe(youmu.auth.uid); wait()
        assert t.take(youmu.events.observe_request) == yuyuko.auth.uid
        yuyuko.observe.observe(youmu.auth.uid); wait()
        assert youmu.events.observe_request not in t

        # Happy path
        youmu.observe.grant(yuyuko.auth.uid, True); wait()
        assert yuyuko.events.game_joined in t

        # Observers should not interference legit game players
        yuyuko.room.get_ready(); wait()
        assert youmu.events.game_started not in t
        assert yuyuko.events.game_started not in t

        # Kick observer
        t.clear()
        youmu.observe.kick(yuyuko.auth.uid); wait()
        assert t.take(yuyuko.events.game_left)

        # Big brother
        s.observe.add_bigbrother(yuyuko.auth.uid)
        yuyuko.observe.observe(youmu.auth.uid); wait()
        assert yuyuko.events.game_joined in t

        # Stop observing
        t.clear()
        yuyuko.room.leave(); wait()
        assert yuyuko.events.game_left in t

        # Big brother, again
        s.observe.add_bigbrother(yuyuko.auth.uid)
        yuyuko.observe.observe(youmu.auth.uid); wait()
        assert yuyuko.events.game_joined in t

        # Observee exits
        t.clear()
        youmu.room.leave(); wait()
        assert t.take(youmu.events.game_left)
        assert t.take(yuyuko.events.game_left)
        assert s.lobby.state_of(s.lobby.get(youmu.auth.uid)) == 'lobby'
        assert s.lobby.state_of(s.lobby.get(yuyuko.auth.uid)) == 'lobby'

        # Stop being big brother
        s.observe.remove_bigbrother(yuyuko.auth.uid)

        # Happy path
        t.clear()
        youmu.room.create('Boom', 'THBattleDummy1', {}); wait()
        yuyuko.observe.observe(youmu.auth.uid); wait()
        youmu.observe.grant(yuyuko.auth.uid, True); wait()
        youmu.room.get_ready(); wait()
        assert not youmu.game.is_observe(t[youmu.events.game_started])
        assert yuyuko.game.is_observe(t[yuyuko.events.game_started])
        youmu.game.start_game(t[youmu.events.game_started])
        yuyuko.game.start_game(t[yuyuko.events.game_started])
        wait()
        assert t.take(youmu.events.game_ended)
        assert t.take(yuyuko.events.game_ended)

        # Happy path, successive game
        assert t.take(youmu.events.game_joined)
        assert t.take(yuyuko.events.game_joined)
        youmu.room.get_ready(); wait()
        assert not youmu.game.is_observe(t[youmu.events.game_started])
        assert yuyuko.game.is_observe(t[yuyuko.events.game_started])
        youmu.game.start_game(t[youmu.events.game_started])
        yuyuko.game.start_game(t[yuyuko.events.game_started])
        wait()
