# -*- coding: utf-8 -*-

# -- stdlib --
from collections import defaultdict
from options import options
from contextlib import contextmanager
import logging
log = logging.getLogger('forum_integration')

# -- third party --
from gevent.queue import Queue
import gevent

# -- own --
from .base import server_side_only
from utils import log_failure


# -- globals --
_member_client = None
_cli_pool = None
_try_counter = 10032


# -- code --
@contextmanager
def member_client_pool():
    global _cli_pool

    if not _cli_pool:
        from utils.rpc import RPCClient
        host, port = options.member_service.split(':')
        port = int(port)
        _cli_pool = Queue(10)
        for i in xrange(10):
            _cli_pool.put(RPCClient((host, port), timeout=6))

    try:
        cli = _cli_pool.get()
        yield cli
    finally:
        _cli_pool.put(cli)


class Account(object):
    is_guest = False

    @classmethod
    @server_side_only
    def authenticate(cls, username, password):
        with member_client_pool() as cli:
            try:
                uid = int(username)
                uid = uid if uid < 100000 else None
            except ValueError:
                uid = None

            if uid == -1:
                acc = cls()
                acc._fill_trygame()
                return acc
            elif uid:
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
    def _fill_trygame(self):
        global _try_counter
        c = _try_counter
        _try_counter += 1

        self.username = u'毛玉' + str(c)
        self.status = 0
        self.userid = -c

        from urlparse import urljoin
        from settings import ACCOUNT_FORUMURL

        self.other = defaultdict(
            lambda: None,
            title=u'不愿注册的毛玉',
            avatar=urljoin(
                ACCOUNT_FORUMURL,
                '/maoyu.png'
            ),
            credits=-998,
            games=0,
            drops=0,
        )

    @server_side_only
    def available(self):
        return self.status != -1

    @server_side_only
    def add_credit(self, type, amount):
        if self.userid < 0:
            return

        @gevent.spawn
        @log_failure(log)
        def worker():
            with member_client_pool() as cli:
                rst = cli.add_credit(self.userid, type, amount)
                rst and self._fill_account(rst)

    @classmethod
    def parse(cls, data):
        acc = cls()
        mode, acc.userid, acc.username, other = data
        acc.other = defaultdict(lambda: None, other)
        assert mode == 'forum'
        return acc

    def __data__(self):
        return ['forum', self.userid, self.username, self.other]

__all__ = ['Account']
