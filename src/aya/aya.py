# -*- coding: utf-8 -*-

# -- prioritized --
import gevent
from gevent import monkey
monkey.patch_all()

# -- stdlib --
from cStringIO import StringIO
from functools import partial
import argparse
import logging
import random
import re
import sys

# -- third party --
from gevent.backdoor import BackdoorServer
from gevent.coros import RLock
from gevent.pool import Pool
import redis

# -- own --
from deathbycaptcha import SocketClient as DBCClient
from qqbot import QQBot
from utils import check, CheckFailed
from utils.interconnect import Interconnect
from utils.misc import GenericPool


# -- code --
parser = argparse.ArgumentParser('aya')
parser.add_argument('--qq', type=int)
parser.add_argument('--password')
parser.add_argument('--dbc-username')
parser.add_argument('--dbc-password')
parser.add_argument('--redis-url', default='redis://localhost:6379')
parser.add_argument('--member-service', default='localhost')
options = parser.parse_args()

log = logging.getLogger('Aya')
pool = Pool(5)

interconnect = None
aya = None

ping_responses = [
    None,
    u'文文在哦',
    u'文文在哦',
    u'文文在哦 (｡´-д-)疲れた。。',
    u'(o´Д`)=з 疲れた･･･',
    u'那个……这样就够了吧……我很忙的……',
    u'对不起……这样会让我很困扰的……请不要再接近我了好吗(￣△￣；)',
    u'明明是一脸恶心丸的画风，为什么还要这么跳呢（；￣д￣）',
    u'(ﾉ｀･ﾛ)ﾉ＜嫌嫌嫌嫌嫌嫌嫌嫌嫌!!!!',
    u'死宅真是讨厌，才不会跟死宅交往(# ﾟДﾟ)つ',
    u'就算是破鞋，也不会找死宅的！！！ヽ(#`Д´)ﾉ┌┛',
]


def clipool_factory():
    from utils.rpc import RPCClient
    return RPCClient((options.member_service, 7000), timeout=6)

member_client_pool = GenericPool(clipool_factory, 10)


class AyaDAO(object):
    def __init__(self):
        self.redis = redis.from_url(options.redis_url)

    def get_binding(self, qq):
        rst = self.redis.hget('aya:binding', int(qq))
        try:
            return int(rst)
        except:
            return None

    def get_binding_r(self, uid):
        rst = self.redis.hget('aya:binding_r', int(uid))
        try:
            return int(rst)
        except:
            return None

    def get_all_bindings(self):
        return self.redis.hgetall('aya:binding')

    def set_binding(self, qq, uid):
        qq, uid = int(qq), int(uid)
        self.redis.hset('aya:binding', qq, uid)
        self.redis.hset('aya:binding_r', uid, qq)

    def is_group_on(self, group_num):
        return self.redis.sismember('aya:group_on', int(group_num))

    def get_all_groups_on(self):
        rst = self.redis.smembers('aya:group_on')
        if not rst:
            return []

        return [int(i) for i in rst]

    def set_group_on(self, group_num):
        self.redis.sadd('aya:group_on', int(group_num))

    def set_group_off(self, group_num):
        self.redis.srem('aya:group_on', int(group_num))

    def incr_ping_count(self, gnum):
        k = 'aya:ping_count:%s' % gnum
        i = self.redis.incr(k)
        self.redis.expire(k, 60)
        return int(i)


dao = AyaDAO()


class Aya(QQBot):
    def on_captcha(self, image):
        logging.info('Solving captcha...')
        f = StringIO()
        f.write(image)
        f.seek(0)
        dbccli = DBCClient(options.dbc_username, options.dbc_password)

        try:
            captcha = dbccli.decode(f, 60)
        except:
            log.exception('Error solving captcha')
            sys.exit(1)

        if captcha:
            self.captcha = captcha
            return captcha['text'], captcha

        sys.exit(1)

    def on_captcha_wrong(self, tag):
        log.info('Captcha wrong!')
        dbccli = DBCClient(options.dbc_username, options.dbc_password)
        dbccli.report(tag['captcha'])

    def on_sess_message(self, msg):
        text = (
            u'文文不认识你，不会理你哦。\n'
            u'加好友的时候验证信息里像这样(文文求交朋友 3456 mima)填上你的论坛uid和密码，不要带括号，文文就会跟你做朋友。'
        )

        self.send_sess_message(msg['id'], msg['from_uin'], text)

    def on_message(self, msg):
        text = (
            u'文文最近很忙，没法跟你闲聊啦……\n'
            u'有空了会告诉你哦～'
        )

        self.send_buddy_message(msg['from_uin'], text)

    def on_group_message(self, msg):
        content = self._plaintext(msg['content']).strip()
        if not content:
            return

        if content.startswith(u'呼叫文文'):
            gnum = self.gcode2groupnum(msg['group_code'])

            if dao.is_group_on(gnum):
                i = dao.incr_ping_count(gnum)
                i = min(i, len(ping_responses) - 1)
                words = ping_responses[i]
            else:
                words = u'哼，有人不让文文说话……'

            pool.apply_async(self.send_group_message, (msg['from_uin'], words))

        elif content == u'文文on':
            superusers = self.get_group_superusers_uin(msg['group_code'])
            if msg['send_uin'] in superusers or self.uin2qq(msg['send_uin']) in (84065234,):
                dao.set_group_on(self.gcode2groupnum(msg['group_code']))
                pool.apply_async(self.send_group_message, (msg['from_uin'], u'收到～文文会以最快速度播报新闻～'))

        elif content == u'文文off':
            gnum = self.gcode2groupnum(msg['group_code'])
            if dao.is_group_on(gnum):
                dao.set_group_off(gnum)
                pool.apply_async(self.send_group_message, (msg['from_uin'], u'哼，不理你们了。管理员叫我我才回来。哼。'))

        elif content[0] in (u'`', u'•'):
            pool.apply_async(self.do_speaker, (msg['send_uin'], content[1:], msg['from_uin']))

    def on_system_message(self, msg):
        pool.apply_async(self.refresh_group_list)

        if msg['type'] == 'verify_required':
            qq = self.uin2qq(msg['from_uin'])

            def fail():
                self.deny_friend_request(qq, u'好友请求填写的不对，文文不要跟你做朋友。')
                return False

            def success():
                self.allow_friend_request(qq)
                self.refresh_buddy_list()
                return True

            req = msg['msg'].split(None, 2)
            req = [i.strip() for i in req]
            try:
                check(len(req) == 3)
                check(req[0] == u'文文求交朋友')
                check(req[1].isdigit())
            except CheckFailed:
                return fail()

            uid = int(req[1])
            pwd = req[2]
            with member_client_pool() as cli:
                member = cli.validate_by_uid(uid, pwd)

            if not member:
                return fail()

            dao.set_binding(qq, uid)

            return success()

        else:
            self.unhandled_event('system_message', msg)

    def do_speaker(self, uin, content, group_uin=None):
        fail_text = u'文文不认识你，才不帮你发新闻呢。想跟文文做朋友么？悄悄地告诉文文吧。'
        insufficient_funds_text = u'你的节操掉了一地，才不帮你发新闻呢。'
        friend_uins = [i['uin'] for i in self.buddy_list]
        if uin not in friend_uins:
            group_uin and self.send_group_message(group_uin, fail_text)
            return

        qq = self.uin2qq(uin)
        uid = dao.get_binding(qq)
        if not uid:
            # not bound, but are friends
            # delete him.
            self.delete_friend(uin)
            self.refresh_buddy_list()
            return

        with member_client_pool() as cli:
            member = cli.get_user_info(uid)
            if member['credits'] < 0:
                group_uin and self.send_group_message(group_uin, insufficient_funds_text)
                return

            # April Fool!
            from datetime import datetime
            import random
            b4 = datetime(2015, 4, 1)
            af = datetime(2015, 4, 2)
            if b4 < datetime.now() < af:
                content += random.choice([
                    u'喵～', u'汪～', u'poi～', u'的说～', u'呱～', u'niconiconi～',
                    u'（PS：灵梦没节操——',
                    u'（PS：油咖喱的脚很臭——',
                    u'（PS：河童喜欢巨大的黄瓜——',
                    u'（PS：妖梦是男孩子——',
                    u'（PS：茨木华扇又在卖自己的本子——',
                    u'（PS：幽香和天子又在做爱做的事——',
                    u'（PS：藤原妹红穿的是男士胖次——',
                    u'（PS：帕秋莉喜欢在房间里练习娇喘——',
                    u'（PS：椛椛想要——',
                    u'（PS：爱丽丝又在扎小人——',
                    u'（PS：有看到小伞和盖伦在酒吧喝酒——',
                    u'（PS：四季的胸还不到A罩杯——',
                    u'（PS：早苗的欧派，赞——',
                    u'（PS：森近霖之助昨天买了好多卫生纸——',
                    u'（PS：咲夜又买了更大号的PAD——',
                    u'（PS：昨天下午菜市场关门了，原因是幽幽子上午去过——',
                    u'（PS：昨天琪露诺和灵乌路空比算数，灵乌路空赢了——',
                    u'（PS：守矢大法好—— 天灭博丽，退博保平安—— 人在做，天在看，毫无节操留祸患—— 上网搜“10万元COS”有真相——',
                ])
            # --------

            interconnect.publish('speaker', [member['username'], content])


class AyaInterconnect(Interconnect):
    lock = None

    def on_message(self, node, topic, message):
        if topic == 'speaker':
            from settings import ServerNames
            username, content = message

            foo = str(random.randint(0x10000000, 0xffffffff))
            content = content.replace('||', foo)
            content = re.sub(r'([\r\n]|\|(c[A-Fa-f0-9]{8}|s[12][A-Fa-f0-9]{8}|[BbIiUuHrRGYW]|LB|DB|![RGOB]))', '', content)
            content = content.replace(foo, '||')

            send = u'{}『文々。新闻』{}： {}'.format(
                ServerNames.get(node, node), username, content,
            )

            groups_on = [int(i) for i in dao.get_all_groups_on()]
            gids = [
                g['gid'] for g in aya.group_list
                if aya.gcode2groupnum(g['code']) in groups_on
            ]

            pool.map_async(lambda f: f(), [
                partial(aya.send_group_message, i, send)
                for i in gids
            ])

        elif topic == 'bugreport':
            C = aya.qq2uin_bycache
            aya.send_buddy_message(C(84065234), message)
            aya.send_buddy_message(C(402796982), message)

        elif topic == 'aya_charge':
            uid, fee = message
            if fee < 50: return
            qq = dao.get_binding_r(uid)
            if not uid: return
            uin = aya.qq2uin_bycache(qq)
            if not uin: return
            aya.send_buddy_message(uin, u'此次文文新闻收费 %s 节操。' % int(fee))

    def publish(self, topic, data):
        lock = self.lock
        if not lock:
            lock = RLock()
            self.lock = lock

        with lock:
            return Interconnect.publish(self, topic, data)


def main():
    global interconnect, aya
    logging.basicConfig(level=logging.DEBUG)

    gevent.spawn(BackdoorServer(('127.0.0.1', 11111)).serve_forever)

    aya = Aya(options.qq, options.password)
    # aya.wait_ready()
    interconnect = AyaInterconnect.spawn('aya', options.redis_url)
    aya.join()


if __name__ == '__main__':
    main()
