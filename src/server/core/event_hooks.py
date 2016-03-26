# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging

# -- third party --
import gevent

# -- own --
from game.autoenv import EventHandler
from db.models import User
from db.session import Session

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
        def add_ppoint():
            # log.info('Add ppoint for %s, +%s', uid, amount)
            try:
                s = Session()
                u = s.query(User).filter(User.id == uid).one()
                u.ppoint += amount
                s.commit()
            except:
                s.rollback()

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
