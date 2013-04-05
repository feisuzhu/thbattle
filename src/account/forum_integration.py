# -*- coding: utf-8 -*-
from collections import defaultdict

from .base import server_side_only


# -- globals --
_member_client = None


# -- code --
def get_member_client():
    global _member_client

    from utils.rpc import RPCClient
    if _member_client:
        return _member_client

    _member_client = RPCClient(('127.0.0.1', 7000), timeout=1)
    return _member_client


class Account(object):

    @classmethod
    @server_side_only
    def authenticate(cls, username, password):
        cli = get_member_client()
        try:
            uid = int(username)
            uid = uid if uid < 100000 else None
        except ValueError:
            uid = None

        if uid:
            member = cli.validate_by_uid(uid, password)
        else:
            member = cli.validate_by_username(username, password)

        if not member:
            return False

        acc = cls()
        acc._fill_account(member)
        return acc

    @server_side_only
    def _fill_account(self, data):
        self.username = data['username'].decode('utf-8')
        self.status = data['status']
        self.userid = data['uid']

        from urlparse import urljoin
        from settings import ACCOUNT_FORUMURL

        self.other = defaultdict(
            lambda: None,
            title=data['title'].decode('utf-8'),
            avatar=urljoin(
                ACCOUNT_FORUMURL,
                '/uc_server/avatar.php?uid=%d&size=middle' % data['uid'],
            ),
            credits=data['credits'],
            games=data['games'],
            drops=data['drops'],
        )

    @server_side_only
    def available(self):
        return self.status != -1

    @server_side_only
    def add_credit(self, type, amount):
        cli = get_member_client()
        rst = cli.add_credit(self.userid, type, amount)
        if rst:
            self._fill_account(rst)

    @classmethod
    def parse(cls, data):
        acc = cls()
        mode, acc.userid, acc.username, other = data
        acc.other = defaultdict(lambda:None, other)
        assert mode == 'forum'
        return acc

    def __data__(self):
        return ['forum', self.userid, self.username, self.other]

__all__ = ['Account']
