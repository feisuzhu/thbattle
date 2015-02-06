# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from functools import wraps
import random

# -- third party --
# -- own --


# -- code --
def server_side_only(f):
    @wraps(f)
    def _wrapper(*a, **k):
        from game.autoenv import Game
        if Game.CLIENT_SIDE:
            raise Exception('Server side only method!')
        return f(*a, **k)
    return _wrapper


class AccountBase(object):

    @classmethod
    def parse(cls, data):
        acc = cls()
        mode, acc.userid, acc.username, other = data
        acc.other = defaultdict(lambda: None, other)
        assert mode == 'forum'
        return acc

    def __data__(self):
        return ['forum', self.userid, self.username, self.other]

    @classmethod
    def build_npc_account(cls, name):
        acc = cls()
        acc.username = name
        acc.userid = -random.randrange(100000, 1000000)

        acc.other = defaultdict(
            lambda: None,
            title=u'文艺的NPC',
            avatar='',
            credits=0,
            games=10000,
            drops=0,
            badges=[],
        )

        return acc
