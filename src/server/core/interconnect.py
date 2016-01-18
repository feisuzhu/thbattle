# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from gevent.pool import Pool
import gevent

# -- own --
from options import options
from server.core.state import ServerState


# -- code --
if options.interconnect:
    from utils.interconnect import Interconnect

    class InterconnectHandler(Interconnect):
        def on_message(self, node, topic, message):
            if topic == 'speaker':
                node = node if node != options.node else ''
                message.insert(0, node)
                Pool(5).map_async(lambda u: u.write(['speaker_msg', message]), ServerState.lobby.users.values())

            elif topic == 'aya_charge':
                uid, fee = message
                user = ServerState.lobby.users.get(uid)
                if not user: return
                gevent.spawn(user.account.refresh)
                gevent.spawn(user.write, ['system_msg', [None, u'此次文文新闻收费 %s 节操' % int(fee)]])

    ServerState.interconnect = InterconnectHandler.spawn(options.node, options.redis_url)

else:
    class DummyInterconnect(object):
        def publish(self, key, message):
            pass

    ServerState.interconnect = DummyInterconnect()
