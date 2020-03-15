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


class TestKedama(object):
    def testKedama(self):
        env = Environ()
        t = EventTap()

        _ = env.server_core()
        proton = env.client_core()
        kedama = env.client_core()
        t.tap(proton, kedama)

        proton.auth.login("Proton")
        kedama.auth.login("")
        wait()

        # Kedama should not create modes not allowed
        assert proton.auth.uid == 2
        assert kedama.auth.uid < 0
        kedama.room.create('Boom', 'THBattle2v2', {})
        wait()
        assert kedama.events.game_joined not in t
        assert t.take(kedama.events.server_error) == 'kedama_limitation'

        # Kedama should not join modes not allowed
        proton.room.create('Meh', 'THBattle2v2', {}); wait()
        g = t.take(proton.events.game_joined)
        gid = proton.game.gid_of(g)
        kedama.room.join(gid); wait()
        assert kedama.events.game_joined not in t
        assert t.take(kedama.events.server_error) == 'kedama_limitation'

        # Kedama can create modes allowed, but can't invite
        proton.room.leave()
        kedama.room.create('Meh', 'THBattleKOF', {}); wait()
        g = t.take(kedama.events.game_joined)
        gid = kedama.game.gid_of(g)
        kedama.room.invite(proton.auth.uid); wait()
        assert t.take(kedama.events.server_error) == 'kedama_limitation'
