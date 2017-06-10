# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from gevent.pool import Pool
import gevent

# -- own --
from options import options
from server.subsystem import Subsystem
from utils.interconnect import RedisInterconnect


# -- code --
class Interconnect(RedisInterconnect):
    def on_message(self, node, topic, message):
        if topic == 'speaker':
            node = node if node != options.node else ''
            message.insert(0, node)
            Pool(5).map_async(lambda u: u.write(['speaker_msg', message[:300]]), Subsystem.lobby.users.values())

        elif topic == 'aya_charge':
            uid, fee = message
            user = Subsystem.lobby.users.get(uid)
            if not user: return
            gevent.spawn(user.account.refresh)
            gevent.spawn(user.write, ['system_msg', [None, u'此次文文新闻收费 %s 节操' % int(fee)]])
