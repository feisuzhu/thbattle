# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- prioritized --
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import gevent
from gevent import monkey
monkey.patch_all()

# -- stdlib --
from cStringIO import StringIO
from functools import partial
import argparse
import datetime
import json
import logging
import random
import re

# -- third party --
from gevent.backdoor import BackdoorServer
from gevent.coros import RLock
from gevent.pool import Pool
import redis
import requests

# -- own --
from account.forum_integration import Account
from qqbot import QQBot
from utils import CheckFailed, check, instantiate
from utils.interconnect import Interconnect
import db
import upyun


# -- code --
@instantiate
class State(object):
    __slots__ = (
        'options',
        'interconnect',
        'aya',
        'dao',
    )

log = logging.getLogger('Aya')
pool = Pool(5)

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


class AyaDAO(object):
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)

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


class Aya(QQBot):
    def on_captcha(self, image):
        from deathbycaptcha import SocketClient as DBCClient
        logging.info('Solving captcha...')
        f = StringIO()
        f.write(image)
        f.seek(0)
        dbccli = DBCClient(State.options.dbc_username, State.options.dbc_password)

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
        from deathbycaptcha import SocketClient as DBCClient
        dbccli = DBCClient(State.options.dbc_username, State.options.dbc_password)
        dbccli.report(tag['captcha'])

    def on_qrcode(self, image):
        filename = '/qrcode/%s.png' % hex(random.getrandbits(100))
        up = upyun.UpYun(State.options.upyun_bucket, State.options.upyun_username, State.options.upyun_password)
        up.put(filename, image)
        requests.post(State.options.bearybot, headers={'Content-Type': 'application/json'}, data=json.dumps({
            'text': 'QRCode Login for Aya the QQBot',
            'attachments': [{
                'color': '#ffa500',
                'images': [{'url': 'http://%s.b0.upaiyun.com%s' % (State.options.upyun_bucket, filename)}],
                'title': datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S'),
                'text': 'Meh...',
            }],
        }))

    def _message(self, type, msg):
        not_registered_text = (
            u'文文不认识你，不会帮你发新闻的哦。\n'
            u'回复“文文求交朋友 <uid> <密码>”，不要带引号，文文就会认识你啦。\n'
            u'uid可以在登陆论坛或者游戏后知道，密码就是论坛的密码。\n'
            u'比如这样：\n'
            u'文文求交朋友 23333 wodemima23333\n'
            u'\n'
            u'文文帮你发新闻是要收费的，一发5节操。不过连续发的话收费会翻倍哦。'
        )

        registered_text = (
            u'哎呀呀呀，原来你是%s啊，文文认识你了。\n'
            u'只要你的节操还在，文文就会帮你发新闻～\n'
        )

        help_text = (
            u'所有在QQ群里以“`”或者“\'”开头的聊天都会被当做发新闻的请求～\n'
            u'比如这样：\n'
            u'`文文最是清正廉直！\n'
            u'\n'
            u'文文帮你发新闻是要收费的，一发5节操。不过连续发的话收费会翻倍哦。'
        )

        fail_text = (
            u'文文调查了一下你，发现你的密码填的不对！\n'
            u'快说你到底是谁！'
        )

        qq = self.uin2qq(msg['from_uin'])

        if type == 'buddy':
            send = lambda t: self.send_buddy_message(msg['from_uin'], t)
        elif type == 'sess':
            send = lambda t: self.send_sess_message(msg['id'], msg['from_uin'], t)

        uid = State.dao.get_binding(qq)
        if not uid:
            content = self._plaintext(msg['content']).strip()
            req = content.split(None, 2)
            req = [i.strip() for i in req]
            try:
                check(len(req) == 3)
                check(req[0] == u'文文求交朋友')
                check(req[1].isdigit())
            except CheckFailed:
                send(not_registered_text)
                return

            uid = int(req[1])
            pwd = req[2]

            username = None
            user = Account.find(uid)
            if not (user and Account.validate_by_password(user.dz_member, pwd)):
                send(fail_text)
                return
            username = user.username

            State.dao.set_binding(qq, uid)

            send(registered_text % username + help_text)
            return

        send(help_text)

    on_message = lambda self, msg: self._message('buddy', msg)
    on_sess_message = lambda self, msg: self._message('sess', msg)

    def on_group_message(self, msg):
        content = self._plaintext(msg['content']).strip()
        if not content:
            return

        if content.startswith(u'呼叫文文'):
            gnum = self.gcode2groupnum(msg['group_code'])

            if State.dao.is_group_on(gnum):
                i = State.dao.incr_ping_count(gnum)
                i = min(i, len(ping_responses) - 1)
                words = ping_responses[i]
            else:
                words = u'哼，有人不让文文说话……'

            pool.apply_async(self.send_group_message, (msg['from_uin'], words))

        elif content == u'文文on':
            superusers = self.get_group_superusers_uin(msg['group_code'])
            if msg['send_uin'] in superusers or self.uin2qq(msg['send_uin']) in (84065234,):
                State.dao.set_group_on(self.gcode2groupnum(msg['group_code']))
                pool.apply_async(self.send_group_message, (msg['from_uin'], u'收到～文文会以最快速度播报新闻～'))

        elif content == u'文文off':
            gnum = self.gcode2groupnum(msg['group_code'])
            if State.dao.is_group_on(gnum):
                State.dao.set_group_off(gnum)
                pool.apply_async(self.send_group_message, (msg['from_uin'], u'哼，不理你们了。管理员叫我我才回来。哼。'))

        elif content[0] in (u'`', u"'"):
            pool.apply_async(self.do_speaker, (msg['send_uin'], content[1:], msg['from_uin']))

    def do_speaker(self, uin, content, group_uin=None):
        fail_text = u'文文不认识你，才不帮你发新闻呢。想跟文文做朋友么？悄悄地告诉文文吧。'
        insufficient_funds_text = u'你的节操掉了一地，才不帮你发新闻呢。'

        qq = self.uin2qq(uin)
        uid = State.dao.get_binding(qq)
        if not uid:
            group_uin and self.send_group_message(group_uin, fail_text)
            return

        user = Account.find(uid)
        username = user.username

        if user.jiecao < 0:
            group_uin and self.send_group_message(group_uin, insufficient_funds_text)
            return

        # April Fool!
        from datetime import datetime
        import random
        b4 = datetime(2016, 4, 1)
        af = datetime(2016, 4, 2)
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

            State.interconnect.publish('speaker', [username, content])


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

            groups_on = [int(i) for i in State.dao.get_all_groups_on()]
            gids = [
                g['gid'] for g in State.aya.group_list
                if State.aya.gcode2groupnum(g['code']) in groups_on
            ]

            pool.map_async(lambda f: f(), [
                partial(State.aya.send_group_message, i, send)
                for i in gids
            ])

        elif topic == 'aya_charge':
            uid, fee = message
            if fee < 50: return
            qq = State.dao.get_binding_r(uid)
            if not uid: return
            uin = State.aya.qq2uin_bycache(qq)
            if not uin: return
            State.aya.send_buddy_message(uin, u'此次文文新闻收费 %s 节操。' % int(fee))

    def publish(self, topic, data):
        lock = self.lock
        if not lock:
            lock = RLock()
            self.lock = lock

        with lock:
            return Interconnect.publish(self, topic, data)


def main():
    parser = argparse.ArgumentParser('aya')
    parser.add_argument('--dbc-username')
    parser.add_argument('--dbc-password')
    parser.add_argument('--bearybot')
    parser.add_argument('--upyun-bucket')
    parser.add_argument('--upyun-username')
    parser.add_argument('--upyun-password')
    parser.add_argument('--redis-url', default='redis://localhost:6379')
    parser.add_argument('--db', default='sqlite3:////dev/shm/thb.sqlite3')
    State.options = options = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    db.session.init(options.db)
    gevent.spawn(BackdoorServer(('127.0.0.1', 11111)).serve_forever)

    State.aya = Aya()
    # State.aya.wait_ready()
    State.interconnect = AyaInterconnect.spawn('aya', options.redis_url)
    State.dao = AyaDAO(options.redis_url)
    State.aya.join()


if __name__ == '__main__':
    main()
