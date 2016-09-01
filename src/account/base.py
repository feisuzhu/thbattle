# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from functools import wraps
import random
import logging

# -- third party --
import gevent

# -- own --
from utils import log_failure
from db import transactional


# -- code --
log = logging.getLogger('accout_base')


def server_side_only(f):
    return f  # Meh...

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
        )

        return acc

    @classmethod
    @server_side_only
    def add_user_credit(cls, user, lst, negcheck=None):
        for type, amount in lst:
            if type in ('jiecao', 'games', 'drops', 'ppoint'):
                total = getattr(user, type) + amount
                print getattr(user, type), amount, total
                if negcheck and total < 0:
                    raise negcheck

                setattr(user, type, total)

    @server_side_only
    def add_credit(self, lst):
        @gevent.spawn
        @log_failure(log)
        @transactional()
        def worker():
            uid = self.userid
            user = self.find(uid)
            self.add_user_credit(user, lst)
            self.refresh()
