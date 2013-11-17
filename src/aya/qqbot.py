# -*- coding: utf-8 -*-

import json
import time
import struct
import random
import logging
import requests
import itertools
from collections import defaultdict

log = logging.getLogger('QQBot')


class QQBot(object):
    def __init__(self, qq, password, v=20130916001, appid=501004106):
        self.qq = str(qq)
        self.password = password
        self.logged_in = False
        self.tick = itertools.count(random.randrange(20000000, 30000000))
        self.clientid = random.randrange(30000000, 100000000)
        self.v = v  # nonsense, copied from smartqq
        self.appid = appid  # nonsense, copied from smartqq

        # [{"flag":167773201,"name":"圣维亚学院","gid":3672457874,"code":1705326190}, ...]
        self.group_list = []

        # [{"face":3,"flag":276841024,"nick":"Proton","uin":2462992553}, ...]
        self.buddy_list = []

        self.cache = defaultdict(dict)

        self.session = requests.session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/28.0.1500.71 Chrome/28.0.1500.71 Safari/537.36'
        })

        self.init()

    def init(self):
        pass

    def _stage1_login(self):
        self.group_list[:] = []
        self.buddy_list[:] = []
        self.cache = defaultdict(dict)

        session = self.session
        log.debug('Querying for captcha...')
        check = session.get('https://ssl.ptlogin2.qq.com/check', params={
            'uin': self.qq, 'appid': self.appid,
            'u1': 'http://w.qq.com/proxy.html',
            'js_ver': 10051,
            'js_type': 0,
            'r': random.random(),
        })

        assert check.ok

        state, vc, hexuin = self._jsonp2list(check.content)

        if state == '1':
            # needs captcha
            log.debug('Captcha needed, getting captcha image...')
            captcha = session.get('https://ssl.captcha.qq.com/getimage', params={
                'uin': self.qq, 'aid': self.appid, 'r': random.random()
            })

            assert captcha.ok

            vc, vctag = self.on_captcha(captcha.content)

        hexuin = hexuin.replace('\\x', '').decode('hex')
        log.debug('Do stage1 login...')
        login = session.get('https://ssl.ptlogin2.qq.com/login', params={
            'u': self.qq, 'p': self._encode_password(hexuin, self.password, vc),
            'verifycode': vc, 'aid': self.appid,

            'webqq_type': 10, 'remember_uin': 1, 'login2qq': 1,
            'u1': 'http://w.qq.com/proxy.html?login2qq=1&webqq_type=10',
            'h': 1, 'ptredirect': 0, 'ptlang': 2052,
            'daid': 164, 'from_ui': 1, 'pttype': 1, 'dumy': '',
            'fp': 'loginerroralert', 'action': '0-28-83753',
            'mibao_css': 'm_webqq', 't': 2, 'g': 1, 'js_type': 0, 'js_ver': 10051,
        })

        state, _, url, _, msg, _ = self._jsonp2list(login.content)
        state = int(state)
        if state == 4:
            # captcha wrong
            log.error('Captcha wrong, stage1 login failed.')
            self.on_captcha_wrong(vctag)
            return False
        elif state != 0:
            raise Exception(msg)

        session.get(url)

        self.skey = session.cookies['skey']
        self.original_ptwebqq = self.ptwebqq = session.cookies['ptwebqq']

        return True

    def _stage2_login(self):
        session = self.session
        payload = json.dumps({
            'status': 'online',
            'ptwebqq': self.ptwebqq,
            'clientid': self.clientid,
            'psessionid': '',
        })

        log.debug('Do stage2 login...')
        rst = session.post(
            'http://d.web2.qq.com/channel/login2', data={'r': payload},
            headers={
                'Referer': 'http://d.web2.qq.com/proxy.html?v=%s&callback=1&id=2' % self.v,
                'Origin': 'http://d.web2.qq.com',
            },
        )

        result = json.loads(rst.content)['result']
        self.vfwebqq = result['vfwebqq']
        self.psessionid = result['psessionid']
        self.status = result['status']

    def login(self):
        while True:
            if self._stage1_login():
                break

        self._stage2_login()

        self.logged_in = True
        self.on_login()

    def loop(self):
        session = self.session

        # login
        self.login()

        # poll
        log.debug('Logged in. Begin polling...')

        while True:
            payload = {
                'clientid': self.clientid,
                'psessionid': self.psessionid,
                'key': '',
                'ptwebqq': self.ptwebqq,
            }

            rst = session.post(
                'http://d.web2.qq.com/channel/poll2', data={'r': json.dumps(payload)},
                headers={'Referer': 'http://d.web2.qq.com/proxy.html?v=%s&callback=1&id=3' % self.v}
            )

            assert rst.ok

            rst = json.loads(rst.content)

            code = int(rst['retcode'])

            if code == 102:
                continue

            elif code == 116:
                log.debug('Refresh ptwebqq')
                self.ptwebqq = rst['p']

            elif code in (103, 109, 121, 100006, 100001):
                # {u'retcode': 121, u't': u'0'}
                log.debug('Need relogin')
                self.login()

            # elif code == 109:
            #     log.warning('Unknown code 109: %r', rst)

            elif code == 0:
                messages = rst['result']
                for m in messages:
                    t = m['poll_type']
                    v = m['value']
                    f = getattr(self, 'on_' + t, None)
                    if f:
                        self.polling_hook(f, v)
                    else:
                        log.warning('Unhandled event: <%s> = %r', t, v)

            else:
                log.error('Unknown retcode: %r', rst)

    def polling_hook(self, f, v):
        f(v)

    def refresh_group_list(self):
        assert self.logged_in
        log.debug('Refreshing group info...')

        session = self.session
        payload = {'vfwebqq': self.vfwebqq}
        rst = session.post(
            'http://s.web2.qq.com/api/get_group_name_list_mask2',
            data={'r': json.dumps(payload)},
            headers={
                'Origin': 'http://s.web2.qq.com',
                'Referer': 'http://s.web2.qq.com/proxy.html?v=%s&callback=1&id=3' % self.v,
            }
        )

        assert rst.ok

        rst = json.loads(rst.content)
        if int(rst['retcode']) != 0:
            log.error('Error %r', rst)
            return

        self.group_list[:] = rst['result']['gnamelist']
        return self.group_list

    def refresh_buddy_list(self):
        assert self.logged_in
        log.debug('Refreshing buddy info...')

        session = self.session

        # should use original ptwebqq
        payload = {
            'vfwebqq': self.vfwebqq,
            'hash': self._buddylist_hash(self.qq, self.original_ptwebqq),
        }

        rst = session.post(
            'http://s.web2.qq.com/api/get_user_friends2',
            data={'r': json.dumps(payload)},
            headers={
                'Origin': 'http://s.web2.qq.com',
                'Referer': 'http://s.web2.qq.com/proxy.html?v=%s&callback=1&id=3' % self.v,
            }
        )

        assert rst.ok

        rst = json.loads(rst.content)
        if int(rst['retcode']) != 0:
            log.error('Error %r', rst)
            return

        self.buddy_list[:] = rst['result']['info']

        return self.buddy_list

    def get_group_info_ext(self, gcode):
        assert self.logged_in

        cache = self.cache['group_info_ext']
        if gcode in cache:
            return cache[gcode]

        log.debug('Getting ext group info for gcode %d...', gcode)

        session = self.session
        params = {
            'gcode': gcode,
            'vfwebqq': self.vfwebqq,
            'cb': 'undefined',
            't': int(time.time() * 1000),
        }

        rst = session.get(
            'http://s.web2.qq.com/api/get_group_info_ext2', params=params,
            headers={
                'Origin': 'http://s.web2.qq.com',
                'Referer': 'http://s.web2.qq.com/proxy.html?v=%s&callback=1&id=3' % self.v,
            }
        )

        assert rst.ok

        rst = json.loads(rst.content)
        if int(rst['retcode']) != 0:
            log.error('Error %r', rst)
            return

        cache[gcode] = rst['result']
        return rst['result']

    def get_group_superusers_uin(self, gcode):
        ginfo = self.get_group_info_ext(gcode)
        l = [ginfo['ginfo']['owner']]
        for m in ginfo['ginfo']['members']:
            if m['mflag'] & 1:
                l.append(m['muin'])

        return l

    def _default_handler(t):
        def wrapper(self, v):
            log.info('Message <%s> received: %r', t, v)

        return wrapper

    # <message> =
    # {u'content': [[u'font',
    #    {u'color': u'000000',
    #     u'name': u'\u5b8b\u4f53',
    #     u'size': 10,
    #     u'style': [0, 0, 0]}],
    #   u'\u963f\u65af\u987f\u53d1\u751f\u5730\u65b9 '],
    #  u'from_uin': 3891407156,
    #  u'msg_id': 22041,
    #  u'msg_id2': 968626,
    #  u'msg_type': 9,
    #  u'reply_ip': 178849313,
    #  u'time': 1383456339,
    #  u'to_uin': 2290168915}

    # <message> =
    # {u'content': [[u'font',
    #    {u'color': u'000000',
    #     u'name': u'\u5b8b\u4f53',
    #     u'size': 10,
    #     u'style': [0, 0, 0]}],
    #   u'\u963f\u65af\u8482\u82ac',
    #   [u'offpic',
    #    {u'file_path': u'/d01c8248-0086-40d1-8679-f2f39bb4bf33', u'success': 1}],
    #   u'\u963f\u65af\u987f\u53d1\u70e7\r',
    #   [u'offpic',
    #    {u'file_path': u'/39b75fd0-923d-4fe3-9e73-4fe1e9ec64cc', u'success': 1}],
    #   u' '],
    #  u'from_uin': 3891407156,
    #  u'msg_id': 22042,
    #  u'msg_id2': 10890,
    #  u'msg_type': 9,
    #  u'reply_ip': 178849313,
    #  u'time': 1383456553,
    #  u'to_uin': 2290168915}
    on_message = _default_handler('message')

    # <group_message> =
    # {u'content': [[u'font',
    # {u'color': u'000000',
    #     u'name': u'\u5b8b\u4f53',
    #     u'size': 10,
    #     u'style': [0, 0, 0]}],
    # u'@\u6587\u6587  '],
    # u'from_uin': 921020219,
    # u'group_code': 952880722,
    # u'info_seq': 244369943,
    # u'msg_id': 20815,
    # u'msg_id2': 8639,
    # u'msg_type': 43,
    # u'reply_ip': 176756624,
    # u'send_uin': 3891407156,
    # u'seq': 216858,
    # u'time': 1383448210,
    # u'to_uin': 2290168915}
    on_group_message = _default_handler('group_message')

    on_discu_message = _default_handler('discu_message')

    # <sess_message> =
    # {u'content': [[u'font',
    #    {u'color': u'800080',
    #     u'name': u'\u5b8b\u4f53',
    #     u'size': 9,
    #     u'style': [1, 0, 0]}],
    #   u'123321 '],
    #  u'flags': {u'audio': 1, u'file': 1, u'pic': 1, u'text': 1, u'video': 1},
    #  u'from_uin': 1944240919,
    #  u'id': 192632011,
    #  u'msg_id': 8961,
    #  u'msg_id2': 144412,
    #  u'msg_type': 140,
    #  u'reply_ip': 178848397,
    #  u'ruin': 2534869498,
    #  u'service_type': 0,
    #  u'time': 1383480590,
    #  u'to_uin': 2986902553}
    on_sess_message = _default_handler('sess_message')

    # <shake_message> =
    # {u'from_uin': 3891407156,
    #  u'msg_id': 22040,
    #  u'msg_id2': 317425,
    #  u'msg_type': 9,
    #  u'reply_ip': 178847891,
    #  u'to_uin': 2290168915}
    on_shake_message = _default_handler('shake_message')

    # <system_message/friend_request> =
    # {u'result': [{u'poll_type': u'system_message',
    #    u'value': {u'account': 2986902553,
    #     u'allow': 1,
    #     u'client_type': 1,
    #     u'from_uin': 3379597260,
    #     u'msg': u'verify info',
    #     u'seq': 51448,
    #     u'stat': 10,
    #     u'type': u'verify_required',
    #     u'uiuin': u''}}],
    #  u'retcode': 0}
    on_system_message = _default_handler('system_message')

    # <input_notify> =
    # {u'from_uin': 3891407156,
    #  u'msg_id': 62944,
    #  u'msg_id2': 1,
    #  u'msg_type': 121,
    #  u'reply_ip': 4294967295,
    #  u'to_uin': 2290168915}
    on_input_notify = _default_handler('input_notify')

    # <buddies_status_change> = {u'status': u'online', u'client_type': 1, u'uin': 3891407156}
    on_buddies_status_change = _default_handler('buddies_status_change')

    # <kick_message> =
    # {u'reason': u'\u60a8\u7684\u8d26\u53f7\u5728\u53e6\u4e00\u5730\u70b9\u767b\u5f55\uff0c\u60a8\u5df2\u88ab\u8feb\u4e0b\u7ebf\u3002\u5982\u6709\u7591\u95ee\uff0c\u8bf7\u767b\u5f55 safe.qq.com \u4e86\u89e3\u66f4\u591a\u3002',
    #  u'show_reason': 1,
    #  u'way': u'poll'}
    def on_kick_message(self, v):
        log.error(u'kicked: %s', v['reason'])
        import sys
        sys.exit()

    def on_captcha(self, image):
        raise Exception('Override this!')

    def on_captcha_wrong(self):
        print 'Wrong captcha!'

    # ----------------

    def send_buddy_message(self, uin, message, font=None):
        log.info('send_buddy_message(%d, %r)', uin, message)
        font = font or {
            'name': u'宋体',
            'size': 10,
            'style': [0, 0, 0],
            'color': '000000',
        }
        msg_id = self.tick.next()
        content = [message, font]

        payload = {
            'to': uin,
            'face': 555,  # wtf is this?
            'content': json.dumps(content),
            'msg_id': msg_id,
            'clientid': self.clientid,
            'psessionid': self.psessionid,
        }

        session = self.session
        session.post(
            'http://d.web2.qq.com/channel/send_buddy_msg2',
            data={'r': json.dumps(payload), 'clientid': self.clientid, 'psessionid': self.psessionid},
            headers={
                'Origin': 'http://d.web2.qq.com',
                'Referer': 'http://d.web2.qq.com/proxy.html?v=%s&callback=1&id=3' % self.v,
            }
        )

    def send_group_message(self, group_uin, message, font=None):
        log.info('send_group_message(%d, %r)', group_uin, message)
        font = font or {
            'name': u'宋体',
            'size': 10,
            'style': [0, 0, 0],
            'color': '000000',
        }
        msg_id = self.tick.next()
        content = [message, font]

        payload = {
            'group_uin': group_uin,
            'content': json.dumps(content),
            'msg_id': msg_id,
            'clientid': str(self.clientid),
            'psessionid': self.psessionid,
        }

        session = self.session

        session.post(
            'http://d.web2.qq.com/channel/send_qun_msg2',
            data={'r': json.dumps(payload), 'clientid': self.clientid, 'psessionid': self.psessionid},
            headers={
                'Origin': 'http://d.web2.qq.com',
                'Referer': 'http://d.web2.qq.com/proxy.html?v=%s&callback=1&id=3' % self.v,
            }
        )

    def send_sess_message(self, group_id, uin, message, font=None):
        # NOTE: group_id(==group_uin), gcode, and group number is not the same thing
        log.info('send_sess_message(%d, %d, %r)', group_id, uin, message)
        font = font or {
            'name': u'宋体',
            'size': 10,
            'style': [0, 0, 0],
            'color': '000000',
        }
        msg_id = self.tick.next()
        content = [message, font]

        gsig = self._get_c2cmsg_sig(group_id, uin)

        payload = {
            'clientid': self.clientid,
            'content': json.dumps(content),
            'face': 558,
            'group_sig': gsig,
            'msg_id': msg_id,
            'psessionid': self.psessionid,
            'service_type': 0,
            'to': uin,
        }

        session = self.session
        session.post(
            'http://d.web2.qq.com/channel/send_sess_msg2',
            data={'r': json.dumps(payload), 'clientid': self.clientid, 'psessionid': self.psessionid},
            headers={
                'Origin': 'http://d.web2.qq.com',
                'Referer': 'http://d.web2.qq.com/proxy.html?v=%s&callback=1&id=3' % self.v,
            }
        )

    def _get_c2cmsg_sig(self, group_id, uin):
        cache = self.cache['c2cmsg']
        if group_id in cache:
            return cache[(group_id, uin)]

        log.debug('Getting c2cmsg sig for group=%d, uin=%d', group_id, uin)

        params = {
            'id': group_id,
            'to_uin': uin,
            'service_type': 0,
            'clientid': self.clientid,
            'psessionid': self.psessionid,
            't': int(time.time()*1000),
        }

        resp = self.session.get(
            'http://d.web2.qq.com/channel/get_c2cmsg_sig2', params=params,
            headers={
                'Origin': 'http://d.web2.qq.com',
                'Referer': 'http://d.web2.qq.com/proxy.html?v=%s&callback=1&id=3' % self.v,
            }
        )

        rst = json.loads(resp.content)
        if rst['retcode']:
            log.error('Error in get_c2cmsg_sig: %r', rst)
            return ''

        rst = rst['result']['value']
        cache[(group_id, uin)] = rst
        return rst

    def _uin2account(self, uin, type, cache, verifysession='', code='', vctag=0):
        uin = int(uin)
        cache = self.cache[cache]
        if uin in cache:
            return cache[uin]

        session = self.session
        params = {
            'tuin': uin,
            'verifysession': verifysession,
            'type': type,
            'vfwebqq': self.vfwebqq,
            'code': code,
            't': int(time.time() * 1000),
        }

        resp = session.get(
            'http://s.web2.qq.com/api/get_friend_uin2',
            params=params,
            headers={'Referer': 'http://s.web2.qq.com/proxy.html?v=%s&callback=1&id=1' % self.v},
        )

        assert resp.ok

        rst = json.loads(resp.content)
        rcode = rst['retcode']

        if rcode == 0:
            cache[uin] = rst['result']['account']
            return rst['result']['account']
        elif rcode in (1000, 1001):
            # captcha needed
            if rcode == 1001:
                self.on_captcha_wrong(vctag)

            privsess = requests.session()
            captcha = privsess.get('http://captcha.qq.com/getimage', params={'aid': self.appid})
            verifysession = privsess.cookies['verifysession']
            vc, vctag = self.on_captcha(captcha.content)
            return self._uin2account(uin, type, cache, verifysession, vc, vctag)
        else:
            assert False, 'Unexpected retcode %d' % rcode

    uin2qq = lambda self, uin: self._uin2account(uin, 1, 'uin2qq')
    gcode2groupnum = lambda self, gcode: self._uin2account(gcode, 4, 'gcode2groupnum')

    def allow_friend_request(self, qq):
        log.info(u'Accepting friend request: %d', qq)
        payload = {
            'account': qq,
            'gid': 0,
            'mname': '',
            'vfwebqq': self.vfwebqq,
        }

        self.session.post(
            'http://s.web2.qq.com/api/allow_and_add2',
            data={'r': json.dumps(payload)},
            headers={'Referer': 'http://s.web2.qq.com/proxy.html?v=%s&callback=1&id=1' % self.v},
        )

    def deny_friend_request(self, qq, reason=''):
        log.info(u'Denying friend request: %d, %s', qq, reason)
        payload = {
            'account': qq,
            'msg': reason,
            'vfwebqq': self.vfwebqq,
        }

        self.session.post(
            'http://s.web2.qq.com/api/deny_added_request2',
            data={'r': json.dumps(payload)},
            headers={'Referer': 'http://s.web2.qq.com/proxy.html?v=%s&callback=1&id=1' % self.v},
        )

    def delete_friend(self, uin):
        log.info(u'Deleting friend: %d', self.uin2qq(uin))
        try:
            del self.cache['uin2qq'][uin]
        except:
            pass

        payload = {
            'tuin': uin,
            'delType': 2,
            'vfwebqq': self.vfwebqq,
        }

        self.session.post(
            'http://s.web2.qq.com/api/delete_friend', data=payload,
            headers={'Referer': 'http://s.web2.qq.com/proxy.html?v=%s&callback=1&id=1' % self.v},
        )

    # ----------------

    @staticmethod
    def _encode_password(uin, passwd, vc):
        from hashlib import md5 as _md5
        md5 = lambda x: _md5(x).digest()
        md5hex = lambda x: md5(x).encode('hex').upper()
        return md5hex(md5hex(md5(passwd) + uin) + vc.upper())

    @staticmethod
    def _jsonp2list(jsonp):
        args = jsonp[jsonp.find('(') + 1: jsonp.rfind(')')]
        return [i.strip("' ") for i in args.split(',')]

    @staticmethod
    def _plaintext(content):
        l = [i for i in content if isinstance(i, basestring)]
        return u''.join(l)

    @staticmethod
    def _buddylist_hash(qq, ptwebqq):
        L = list(struct.unpack('BBBB', struct.pack('>I', int(qq))))
        T = [ord(i) for i in ptwebqq]
        V = [(0, len(T) - 1)]

        while V:
            s, e = V.pop()
            if (s >= e or s < 0 or e >= len(T)):
                continue

            if s + 1 == e:
                if T[s] > T[e]: T[s], T[e] = T[e], T[s]
                continue

            Z = s
            U = e
            ba = T[s]
            while s < e:
                while s < e and T[e] >= ba:
                    e -= 1
                    L[0] = (L[0] + 3) & 255
                if s < e:
                    T[s] = T[e]
                    s += 1
                    L[1] = (L[1] * 13 + 43) & 255
                while s < e and T[s] <= ba:
                    s += 1
                    L[2] = (L[2] - 3) & 255
                if s < e:
                    T[e] = T[s]
                    e -= 1
                    L[3] = (L[0] ^ L[1] ^ L[2] ^ L[3] + 1) & 255

            T[s] = ba
            V.extend([(Z, s - 1), (s + 1, U)])

        V = struct.pack('BBBB', *L).encode('hex').upper()
        return V

# group admin kicks you
# <sys_g_msg> =
# {u'admin_nick': u'\u521b\u5efa\u8005',
#  u'admin_uin': 1031178679,
#  u'from_uin': 4055931059,
#  u'gcode': 1494214629,
#  u'msg_id': 29561,
#  u'msg_id2': 816530,
#  u'msg_type': 34,
#  u'old_member': 2290168915,
#  u'op_type': 3,
#  u'reply_ip': 176756757,
#  u't_admin_uin': u'',
#  u't_gcode': 244369943,
#  u't_old_member': u'',
#  u'to_uin': 2290168915,
#  u'type': u'group_leave'}

# <buddylist_change> = {u'added_friends': [], u'removed_friends': [{u'uin': 424353965}]}
# <buddylist_change> = {u'added_friends': [{u'groupid': 0, u'uin': 1499465057}], u'removed_friends': []}
