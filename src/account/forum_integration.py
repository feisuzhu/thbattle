# -*- coding: utf-8 -*-
from .base import server_side_only

from collections import defaultdict

class Account(object):

    @classmethod
    @server_side_only
    def authenticate(cls, username, password):
        from .forum_integration_db import UCenterMember
        try:
            qs = UCenterMember.objects.select_related(
                'forum_count', 'forum_member', 'forum_field'
            )
            try:
                uid = int(username)
                uid = uid if uid < 100000 else None
            except ValueError:
                uid = None

            if uid:
                ucmember = qs.get(uid=uid)
            else:
                ucmember = qs.get(username=username)

        except UCenterMember.DoesNotExist:
            return False

        if not ucmember.validate_password(password):
            return False

        acc = cls()
        acc.username = ucmember.username
        acc.userid = ucmember.uid

        from urlparse import urljoin

        from settings import ACCOUNT_FORUMURL

        acc.other = defaultdict(
            lambda: None,
            title=ucmember.forum_field.customstatus,
            avatar=urljoin(ACCOUNT_FORUMURL, '/uc_server/avatar.php?uid=%d&size=middle' % ucmember.uid),
            credits=ucmember.forum_count.extcredits2,
            games=ucmember.forum_count.extcredits8,
        )

        acc.ucmember = ucmember

        return acc

    @server_side_only
    def logout(self):
        pass

    @server_side_only
    def available(self):
        return self.ucmember.forum_member.status != -1

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
