# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging

# -- third party --
import gevent

# -- own --
from game.autoenv import EventHandler
from account import Account
from db.session import transactional

# -- code --
log = logging.getLogger('server.core.event_hooks')


class CollectPPointHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type != 'collect_ppoint':
            return arg

        acc, amount = arg
        uid = acc.userid
        if uid < 0:  # 毛玉
            return arg

        @gevent.spawn
        @transactional()
        def add_ppoint():
            # log.info('Add ppoint for %s, +%s', uid, amount)
            user = Account.find(uid)
            Account.add_user_credit(user, [('ppoint', amount)])

        return arg


class ServerEventHooks(EventHandler):
    def __init__(self):
        self.hooks = [
            CollectPPointHandler(),
        ]

    def handle(self, evt_type, arg):
        for h in self.hooks:
            arg = h.handle(evt_type, arg)

        return arg
