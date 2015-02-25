# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
import random

# -- third party --
# -- own --
from .base import server_side_only, AccountBase


# -- code --
class Account(AccountBase):

    @classmethod
    def authenticate(cls, username, password):
        if len(username) > 0:
            acc = cls()
            acc.username = username
            acc.userid = 1 if username == 'Proton' else random.randint(10, 100000)
            acc.other = defaultdict(
                lambda: None,
                title=u'野生的THB玩家',
                avatar='http://www.thbattle.net/maoyu.png',
                credits=998,
                games=1,
                drops=0,
                badges=['dev', 'contributor'],
            )
            return acc

        return False

    @server_side_only
    def available(self):
        return True

    @server_side_only
    def add_credit(self, type, amount):
        pass

    @server_side_only
    def refresh(self):
        pass

    @server_side_only
    def is_maoyu(self):
        return False
