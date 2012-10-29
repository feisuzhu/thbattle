# -*- coding: utf-8 -*-

from .base import server_side_only
from collections import defaultdict

class Account(object):

    @classmethod
    @server_side_only
    def authenticate(cls, username, password):
        if len(username) > 0:
            acc = cls()
            acc.username = username
            acc.userid = 1 if username == 'Proton' else id(acc)
            acc.other = defaultdict(
                lambda: None,
                title=u'野生的THB玩家',
                avatar=None,
                credits=998,
                games=1,
                drops=0,
            )
            return acc

        return False

    @server_side_only
    def logout(self):
        pass

    @server_side_only
    def available(self):
        return True

    @classmethod
    def parse(cls, data):
        acc = cls()
        mode, acc.userid, acc.username = data
        acc.other = defaultdict(
            lambda: None,
            title=u'野生的THB玩家',
            avatar=None,
            credits=998,
            games=1,
        )
        assert mode == 'freeplay'
        return acc

    def __data__(self):
        return ['freeplay', self.userid, self.username]
