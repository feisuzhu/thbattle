# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
from itertools import count

# -- third party --
# -- own --
from account.base import AccountBase, server_side_only


# -- code --
counter = count(1).next


class Account(AccountBase):

    @classmethod
    def authenticate(cls, username, password):
        acc = cls()
        acc.userid = counter()
        acc.id = acc.userid
        acc.username = str(username)
        acc.email = str(username)
        acc.credits = 998
        acc.games = 1
        acc.drops = 0

        acc.other = defaultdict(
            lambda: None,
            title=u'野生的THB玩家',
            avatar='http://www.thbattle.net/maoyu.png',
            credits=998,
            games=1,
            drops=0,
        )

        return acc

    @staticmethod
    @server_side_only
    def validate_by_password(user, password):
        return True

    @server_side_only
    def available(self):
        return True

    @server_side_only
    def add_credit_sync(self, lst, user=None):
        super(Account, self).add_credit_sync(lst, user)

    @server_side_only
    def refresh(self):
        user = self.find(self.userid)
        self._fill_account(user)

    @server_side_only
    def is_maoyu(self):
        return False

    @classmethod
    @server_side_only
    def add_user_credit(cls, user, lst, negcheck=None):
        pass

    @server_side_only
    def add_credit(self, lst):
        pass
