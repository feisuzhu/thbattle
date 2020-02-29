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


class TestKedama(object):
    def testKedama(self):
        env = Environ()
        t = EventTap()

        _ = env.server_core()
        proton = env.client_core()
        kedama = env.client_core()
        proton.auth.login("Proton")
        kedama.auth.login("")

        wait()

        assert proton.auth.uid == 2
        assert kedama.auth.uid < 0
        t += kedama.events.game_joined
        t += kedama.events.server_error
        kedama.room.create('Boom', 'THBattle2v2', {})
        wait()

        assert kedama.events.game_joined not in t
        assert t.take(kedama.events.server_error) == 'kedama_limitation'

        proton.room.create('Meh', 'THBattle2v2', {})
        t += proton.events.game_joined
        wait()
        g = t.take(proton.events.game_joined)

        gid = proton.game.gid_of(g)
        kedama.room.join(gid)
        wait()

        assert kedama.events.game_joined not in t
        assert t.take(kedama.events.server_error) == 'kedama_limitation'

        proton.room.leave()
        kedama.room.create('Meh', 'THBattleKOF', {})
        wait()

        g = t.take(kedama.events.game_joined)
        gid = kedama.game.gid_of(g)
        kedama.room.invite(proton.auth.uid)
        wait()

        assert t.take(kedama.events.server_error) == 'kedama_limitation'
