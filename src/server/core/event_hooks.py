# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import logging

# -- third party --

# -- own --
from game.autoenv import EventHandler

# -- code --
log = logging.getLogger('server.core.event_hooks')


class ServerEventHooks(EventHandler):
    def __init__(self):
        self.hooks = [
        ]

    def handle(self, evt_type, arg):
        for h in self.hooks:
            arg = h.handle(evt_type, arg)

        return arg
