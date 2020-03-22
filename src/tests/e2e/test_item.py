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


class TestItem(object):
    def testEuropean(self):
        env = Environ()
        t = EventTap()

        s = env.server_core()
        a, b, c, d = [env.client_core() for _ in range(4)]
        t.tap(a, b, c, d)

        a.auth.login("Alice")
        b.auth.login("Bob")
        c.auth.login("Cirno")
        d.auth.login("Daiyousei")
        wait()

        # Can't use non-existent item
        a.room.create('Boom', 'THBattleDummy4', {}); wait()
        gid = a.game.gid_of(t[a.events.game_joined])
        b.room.join(gid)
        c.room.join(gid)
        d.room.join(gid)
        a.room.use_item('whatever-blah-blah'); wait()
        assert t.take(a.events.server_error) == 'invalid_item_sku'

        # Can't use item not applicable to chosen mode
        a.room.use_item('imperial-role:attacker'); wait()
        assert t.take(a.events.server_error) == 'incorrect_game_mode'

        # Can't use item which do not own
        s.backend.items[a.auth.uid] = {'european': 0}
        a.room.use_item('european'); wait()
        assert t.take(a.events.server_error) == 'item_not_found'

        # Happy path
        s.backend.items[a.auth.uid] = {'european': 1}
        a.room.use_item('european'); wait()
        assert t.take(a.events.server_info) == 'use_item_success'

        # 2nd use should conflict
        s.backend.items[b.auth.uid] = {'european': 1}
        b.room.use_item('european'); wait()
        assert t.take(b.events.server_error) == 'european_conflict'

        # Should consume item when game started
        a.room.get_ready()
        b.room.get_ready()
        c.room.get_ready()
        d.room.get_ready()
        wait()
        assert s.backend.items[a.auth.uid]['european'] == 0
        assert s.backend.items[b.auth.uid]['european'] == 1
