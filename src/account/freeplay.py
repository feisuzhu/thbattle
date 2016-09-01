# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
from itertools import count

# -- third party --
# -- own --
from account.base import AccountBase, server_side_only
from db import transactional, current_session


# -- code --
counter = count(1).next


class Account(AccountBase):

    @classmethod
    @transactional()
    def authenticate(cls, username, password):
        from db.models import User

        try:
            uid = int(username)
        except:
            return None

        user = cls.find(username)
        if not user:
            s = current_session()

            user = User()
            user.id = uid
            user.username = str(username)
            user.email = str(username)
            user.credits = 998
            user.games = 1
            user.drops = 0

            s.add(user)
            s.flush()

        return cls()._fill_account(user)

    def _fill_account(acc, user):
        acc.username = user.username
        acc.userid = user.id
        acc.other = defaultdict(
            lambda: None,
            title=u'野生的THB玩家',
            avatar='http://www.thbattle.net/maoyu.png',
            credits=user.jiecao,
            games=user.games,
            drops=user.drops,
        )

        return acc

    @staticmethod
    @server_side_only
    def validate_by_password(user, password):
        return True

    @staticmethod
    @server_side_only
    @transactional()
    def find(id):
        from db.models import User

        s = current_session()

        try:
            uid = int(id)
            uid = uid if uid < 500000 else None
        except ValueError:
            uid = None

        if not uid:
            return None

        q = s.query(User)
        user = q.filter(User.id == uid).first()

        return user

    @server_side_only
    def available(self):
        return True

    @server_side_only
    @transactional()
    def add_credit_sync(self, lst, user=None):
        super(Account, self).add_credit_sync(lst, user)

    @server_side_only
    def refresh(self):
        user = self.find(self.userid)
        self._fill_account(user)

    @server_side_only
    def is_maoyu(self):
        return False
