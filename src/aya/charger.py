# -*- coding: utf-8 -*-

# -- prioritized --
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from gevent import monkey
monkey.patch_all()

# -- stdlib --
from collections import defaultdict
import argparse
import logging
import time

# -- third party --
import gevent

# -- own --
from utils.interconnect import RedisInterconnect
from utils.rpc import RPCClient

# -- code --
member_service = None
log = None
interconnect = None
history = defaultdict(lambda: (0, 5))

privileged = (
    109,   # 红领京巴
    3564,  # 镜
    6584,  # 唯夜
    351,   # 西瓜
    162,   # 灰
    103,   # 八咫乌鸦
    2,     # Proton
)


def charge(username, message):
    user = member_service.get_user_info_by_username(username)
    if not user:
        log.info('User %s not found' % username)
        return

    uid = user['uid']
    if uid in privileged:
        log.info('User %s in privileged group, not charging.' % username)
        return

    t, fee = history[uid]
    now = time.time()
    fee = max(fee - (now - t) / 30.0, 5)
    if not isinstance(message, unicode):
        message = message.decode('utf-8')

    l = len(message)

    fee += 0 if l < 40 else (l - 40) * 1
    history[uid] = (now, min(fee * 2, 2000))
    fee  = int(fee)
    log.info('Charge %s for %s' % (username, fee))
    member_service.add_credit(user['uid'], 'credits', -fee)
    interconnect.publish('aya_charge', [uid, fee])


class Interconnect(RedisInterconnect):
    def on_message(self, node, topic, message):
        if topic == 'speaker':
            gevent.spawn(charge, message[0], message[1])


def main():
    global options, member_service, interconnect, log
    parser = argparse.ArgumentParser('aya_charger')
    parser.add_argument('--redis-url', default='redis://localhost:6379')
    parser.add_argument('--member-service', default='localhost')
    parser.add_argument('--log', default='INFO')
    options = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=getattr(logging, options.log))
    log = logging.getLogger('aya_charger')

    member_service = RPCClient((options.member_service, 7000), timeout=2)
    interconnect = Interconnect.spawn('charger', options.redis_url)

    gevent.hub.get_hub().join()

if __name__ == '__main__':
    main()
