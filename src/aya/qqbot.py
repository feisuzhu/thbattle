# -*- coding: utf-8 -*-

# -- stdlib --
from cStringIO import StringIO
from collections import defaultdict
from socket import socket
import itertools
import json
import urlparse
import logging
import random
import re
import struct
import time

# -- third party --
from gevent.event import Event
from gevent.pool import Pool
from gevent.socket import socket as gsock
import gevent
import requests
import spidermonkey

# -- own --

# -- code --
if gsock is not socket:
    from gevent import monkey
    monkey.patch_all()

log = logging.getLogger('QQBot')

UA_STRING = (
    'Mozilla/5.0 (X11; Linux x86_64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Ubuntu Chromium/28.0.1500.71 '
    'Chrome/28.0.1500.71 Safari/537.36'
)


def naive_qs(d):
    return '&'.join(['%s=%s' % (k, v) for k, v in d.iteritems()])


class QQBot(object):
    def __init__(self, v=20131024001, appid=501004106):
        self.logged_in = False
        self.tick = itertools.count(random.randrange(20000000, 30000000))
        self.cface_tick = itertools.count(1)
        self.clientid = random.randrange(30000000, 100000000)
        self.v = v  # nonsense, copied from smartqq
        self.appid = appid  # nonsense, copied from smartqq

        self.init_js()

        # [{"flag":167773201,"name":"圣维亚学院","gid":3672457874,"code":1705326190}, ...]
        self.group_list = []

        # [{"face":3,"flag":276841024,"nick":"Proton","uin":2462992553}, ...]
        self.buddy_list = []

        self.cache = defaultdict(dict)
        self.session = requests.session()
        self.session.headers.update({
            'User-Agent': UA_STRING,
        })

        self.pool = Pool(10)
        self.corepool = Pool(3)
        self.ready = Event()

        # self.corepool.spawn(self.init)
        self.init()

    def init_js(self):
        self.js_runtime = spidermonkey.Runtime()
        self.js_context = ctx = self.js_runtime.new_context()
        ctx.execute('''
            window = this; dummy = function() { return {}; }
            document = {getElementById: dummy, createElement: dummy}
            navigator = {userAgent: 'Chrome'}; location = {};
            g_href = ''; document.loginform = {};
        ''')

        ctx.execute('g_appid = %s' % self.appid)

        mq_comm = requests.get("https://ui.ptlogin2.qq.com/js/10114/mq_comm.js").content
        # mq_comm = open('/dev/shm/a.js').read()
        ctx.execute(mq_comm)

        ctx.execute('''
            ptui_checkVC = ptuiCB = function() { return [].slice.call(arguments); };
        ''')

    def init(self):
        self.ready.clear()
        self.login()
        self.corepool.spawn(self.loop)

        p = Pool(5)
        p.map(lambda f: f(), [
            self.refresh_buddy_list,
            self.refresh_group_list,
        ])
        self.ready.set()

        p.map_async(self.gcode2groupnum, [g['code'] for g in self.group_list])
        p.map_async(self.uin2qq, [i['uin'] for i in self.buddy_list])

    def shutdown(self):
        self.ready.clear()
        self.pool.kill()
        self.corepool.kill()

    def join(self):
        self.corepool.join()

    def wait_ready(self):
        self.ready.wait()

    def _stage1_login(self):
        self.group_list[:] = []
        self.buddy_list[:] = []
        self.cache = defaultdict(dict)

        session = self.session
        log.debug('Querying login_sig')
        session.get('https://ui.ptlogin2.qq.com/cgi-bin/login', params={
            'daid': '164',
            'target': 'self',
            'style': '16',
            'mibao_css': 'm_webqq',
            'appid': self.appid,
            'enable_qlogin': '0',
            'no_verifyimg': '1',
            's_url': 'http://w.qq.com/proxy.html',
            'f_url': 'loginerroralert',
            'strong_login': '1',
            'login_state': '10',
            't': self.v,
        }).content

        while True:
            log.debug('Querying for qrcode...')
            qrcode = session.get('https://ssl.ptlogin2.qq.com/ptqrshow', params={
                'appid': '501004106', 'e': '0', 'l': 'M', 's': '5',
                'd': '72', 'v': '4', 't': random.random(),
            }).content

            self.on_qrcode(qrcode)

            log.debug('Waiting qrcode...')

            success = False

            while True:
                qrcode = session.get('https://ssl.ptlogin2.qq.com/ptqrlogin', params={
                    'webqq_type': '10', 'remember_uin': '1', 'login2qq': '1',
                    'u1': 'http://w.qq.com/proxy.html?login2qq=1&webqq_type=10',
                    'aid': '501004106', 'ptredirect': '0', 'ptlang': '2052',
                    'daid': '164', 'from_ui': '1', 'pttype': '1', 'dumy': '',
                    'fp': 'loginerroralert', 'action': '0-0-2223', 'mibao_css': 'm_webqq',
                    't': 'undefined', 'g': '1', 'js_type': '0', 'js_ver': '10135',
                    'login_sig': '', 'pt_randsalt': '0',
                })

                state, _, url, _, msg, _ = self.js_context.execute(qrcode.content)
                log.debug(msg)
                if state in ('66', '67'):
                    # valid, in_progress
                    gevent.sleep(5)
                    continue
                elif state in ('65',):
                    # invalid
                    break
                elif state in ('0',):
                    # success
                    success = True
                    break
                else:
                    raise Exception(msg)

            if success:
                break
            else:
                gevent.sleep(20)

        session.get(url)
        qs = urlparse.urlparse(url).query
        self.qq = int(urlparse.parse_qs(qs)['uin'][0])

        self.skey = session.cookies['skey']
        self.original_ptwebqq = self.ptwebqq = session.cookies['ptwebqq']

        return True

    def _stage2_login(self):

        log.debug('Do stage2 login...')

        rst = self.call_server('d:login2', {
            'status': 'online',
            'ptwebqq': self.ptwebqq,
            'clientid': self.clientid,
            'psessionid': '',
        })

        rst = rst['result']
        self.vfwebqq = rst['vfwebqq']
        self.psessionid = rst['psessionid']
        self.status = rst['status']

        # should be in separate func
        rst = self.call_server('d:get_gface_sig2', method='get',
            clientid=self.clientid,
            psessionid=self.psessionid,
        )['result']

        self.gface_key = rst['gface_key']
        self.gface_sig = rst['gface_sig']

    def login(self):
        self.logged_in = False
        while True:
            if self._stage1_login():
                break

        self._stage2_login()

        self.logged_in = True

    def loop(self):
        # poll
        log.debug('Logged in. Begin polling...')

        while True:
            self.ready.wait()

            rst = self.call_server('d:poll2', {
                'clientid': self.clientid,
                'psessionid': self.psessionid,
                'key': '',
                'ptwebqq': self.ptwebqq,
            })

            code = int(rst['retcode'])

            if code == 102:
                continue

            elif code == 116:
                log.debug('Refresh ptwebqq')
                self.ptwebqq = rst['p']

            elif code in (103, 109, 121, 100006, 100001):
                # {u'retcode': 121, u't': u'0'}
                raise Exception('Goes wrong, just fail.')
                log.debug('Need relogin')
                self.ready.clear()
                self.login()
                self.ready.set()

            # elif code == 109:
            #     log.warning('Unknown code 109: %r', rst)

            elif code == 0:
                messages = rst['result']
                for m in messages:
                    t = m['poll_type']
                    v = m['value']
                    self.pool.spawn(getattr(self, 'on_' + t, self.unhandled_event), v)

            else:
                raise Exception('Goes wrong, just fail.')
                log.error('Unknown retcode: %r', rst)

    def unhandled_event(self, type, value):
        log.warning('Unhandled event: <%s> = %r', type, value)

    def refresh_group_list(self):
        assert self.logged_in
        log.debug('Refreshing group info...')

        rst = self.call_server('s:get_group_name_list_mask2', {
            'vfwebqq': self.vfwebqq,
            'hash': self._buddylist_hash(self.qq, self.original_ptwebqq),
        })

        if int(rst['retcode']) != 0:
            log.error('Error %r', rst)
            return

        self.group_list[:] = rst['result']['gnamelist']
        return self.group_list

    def refresh_buddy_list(self):
        assert self.logged_in
        log.debug('Refreshing buddy info...')

        # should use original ptwebqq

        rst = self.call_server('s:get_user_friends2', {
            'vfwebqq': self.vfwebqq,
            'hash': self._buddylist_hash(self.qq, self.original_ptwebqq),
        })

        if int(rst['retcode']) != 0:
            log.error('Error %r', rst)
            return

        self.buddy_list[:] = rst['result']['info']

        return self.buddy_list

    def get_group_info_ext(self, gcode):
        self.ready.wait()

        cache = self.cache['group_info_ext']
        if gcode in cache:
            return cache[gcode]

        log.debug('Getting ext group info for gcode %d...', gcode)

        rst = self.call_server('s:get_group_info_ext2', method='get',
            gcode=gcode,
            vfwebqq=self.vfwebqq,
            cb='undefined',
            t=int(time.time() * 1000),
        )

        if int(rst['retcode']) != 0:
            log.error('Error %r', rst)
            return

        cache[gcode] = rst['result']
        return rst['result']

    def get_group_superusers_uin(self, gcode):
        self.ready.wait()
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

    def on_qrcode(self, image):
        raise Exception('Override this!')

    # ----------------

    def _format_message(self, message, font=None):
        font = font or {
            'name': u'宋体',
            'size': 10,
            'style': [0, 0, 0],
            'color': '000000',
        }
        return [message, '', ['font', font]]

    def send_buddy_message(self, uin, message, font=None):
        self.ready.wait()
        log.info('send_buddy_message(%d, %r)', uin, message)
        msg_id = self.tick.next()
        content = self._format_message(message, font)

        payload = {
            'to': uin,
            'face': 555,  # wtf is this?
            'content': json.dumps(content),
            'msg_id': msg_id,
            'clientid': self.clientid,
            'psessionid': self.psessionid,
        }

        self.call_server('d:send_buddy_msg2', payload, clientid=self.clientid, psessionid=self.psessionid)

    def send_group_message(self, group_uin, message, font=None):
        log.info('send_group_message(%d, %r)', group_uin, message)
        self.ready.wait()
        msg_id = self.tick.next()
        content = self._format_message(message, font)

        payload = {
            'group_uin': group_uin,
            'content': json.dumps(content),
            'msg_id': msg_id,
            'clientid': str(self.clientid),
            'psessionid': self.psessionid,
        }

        self.call_server('d:send_qun_msg2', payload, clientid=self.clientid, psessionid=self.psessionid)

    def send_group_picture(self, group_uin, filename, data=None, file=None):
        fileobj = file or (StringIO(data) if data else open(filename, 'rb'))
        self.ready.wait()

        payload = {
            'from': 'control',
            'f': 'EQQ.Model.ChatMsg.callbackSendPicGroup',
            'vfwebqq': self.vfwebqq,
            'fileid': self.cface_tick.next(),
        }

        resp = self.session.post(
            'http://up.web2.qq.com/cgi-bin/cface_upload',
            params={'time': int(time.time() * 1000)}, data=payload,
            files={'custom_face': (filename, fileobj)},
            headers={
                'Origin': 'http://web2.qq.com',
                'Referer': 'http://web2.qq.com/webqq.html',
                'User-Agent': UA_STRING,
            },
        )
        fileobj.close()

        cfaceid = re.findall(r'''['"]msg['"]: *['"]([^'"]+)['"] *}''', resp.content)[0]
        cfaceid = cfaceid.split()[0]

        font = {
            'name': u'宋体',
            'size': 10,
            'style': [0, 0, 0],
            'color': '000000',
        }
        msg_id = self.tick.next()
        content = [['cface', 'group', cfaceid], '\n', ['font', font]]

        payload = {
            'group_uin': group_uin,
            'content': json.dumps(content),
            'msg_id': msg_id,
            'clientid': str(self.clientid),
            'psessionid': self.psessionid,
            'key': self.gface_key,
            'sig': self.gface_sig,
        }

        self.call_server('d:send_qun_msg2', payload, clientid=self.clientid, psessionid=self.psessionid)

    def send_sess_message(self, group_id, uin, message, font=None):
        # NOTE: group_id(==group_uin), gcode, and group number is not the same thing
        log.info('send_sess_message(%d, %d, %r)', group_id, uin, message)
        self.ready.wait()
        msg_id = self.tick.next()
        content = self._format_message(message, font)

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

        self.call_server('d:send_sess_msg2', payload, clientid=self.clientid, psessionid=self.psessionid)

    def _get_c2cmsg_sig(self, group_id, uin):
        cache = self.cache['c2cmsg']
        if group_id in cache:
            return cache[(group_id, uin)]

        log.debug('Getting c2cmsg sig for group=%d, uin=%d', group_id, uin)
        self.ready.wait()

        rst = self.call_server('d:get_c2cmsg_sig2', method='get',
            id=group_id,
            to_uin=uin,
            service_type=0,
            clientid=self.clientid,
            psessionid=self.psessionid,
            t=int(time.time()*1000),
        )

        if rst['retcode']:
            log.error('Error in get_c2cmsg_sig: %r', rst)
            return ''

        rst = rst['result']['value']
        cache[(group_id, uin)] = rst
        return rst

    def _uin2account(self, uin, type, cache, cache_rev, verifysession='', code='', vctag=0):
        uin = int(uin)
        cache = self.cache[cache]
        if uin in cache:
            return cache[uin]

        cache_rev = self.cache[cache_rev]
        rst = self.call_server('s:get_friend_uin2', method='get',
            tuin=uin,
            verifysession=verifysession,
            type=type,
            vfwebqq=self.vfwebqq,
            code=code,
            t=int(time.time() * 1000),
        )

        rcode = rst['retcode']

        if rcode == 0:
            rst = rst['result']['account']
            cache[uin] = rst
            cache_rev[rst] = uin
            return rst
        elif rcode in (1000, 1001):
            # captcha needed
            if rcode == 1001:
                self.on_captcha_wrong(vctag)

            verifysession, vc, vctag = self._new_verify_session()
            return self._uin2account(uin, type, cache, cache_rev, verifysession, vc, vctag)
        else:
            assert False, 'Unexpected retcode %d' % rcode

    def _new_verify_session(self):
        privsess = requests.session()
        captcha = privsess.get('http://captcha.qq.com/getimage', params={'aid': self.appid})
        verifysession = privsess.cookies['verifysession']
        vc, vctag = self.on_captcha(captcha.content)
        return verifysession, vc, vctag

    uin2qq = lambda self, uin: self._uin2account(uin, 1, 'uin2qq', 'qq2uin')
    gcode2groupnum = lambda self, gcode: self._uin2account(gcode, 4, 'gcode2groupnum', 'groupnum2gcode')
    qq2uin_bycache = lambda self, qq: self.cache['qq2uin'].get(qq)

    def allow_friend_request(self, qq):
        log.info(u'Accepting friend request: %d', qq)
        self.ready.wait()
        self.call_server('s:allow_and_add2', {
            'account': qq,
            'gid': 0,
            'mname': '',
            'vfwebqq': self.vfwebqq,
        })

    def deny_friend_request(self, qq, reason=''):
        log.info(u'Denying friend request: %d, %s', qq, reason)
        self.ready.wait()
        self.call_server('s:deny_added_request2', {
            'account': qq,
            'msg': reason,
            'vfwebqq': self.vfwebqq,
        })

    def delete_friend(self, uin):
        log.info(u'Deleting friend: %d', self.uin2qq(uin))
        self.ready.wait()
        try:
            del self.cache['uin2qq'][uin]
        except:
            pass

        self.call_server('s:delete_friend', tuin=uin, delType=2, vfwebqq=self.vfwebqq)

    def search_and_add(self, qq, verify_msg):
        log.info(u'Search and add: %d', qq)
        self.ready.wait()
        verifysession, vc, vctag = self._new_verify_session()

        rst = self.call_server('s:search_qq_by_uin2', method='get',
            tuin=qq,
            verifysession=verifysession,
            code=vc,
            vfwebqq=self.vfwebqq,
            t=int(time.time() * 1000),
        )

        if rst['result'] in (1000, 1001, 100000):
            # Wrong captcha? perhaps.
            # Not reporting wrong captcha for safety
            time.sleep(1)
            return self.search_qq_by_uin2(qq, verify_msg)

        token = rst['result']['token']

        rst = self.call_server('s:add_need_verify2', {
            'account': qq,
            'myallow': 1,
            'groupid': 1,
            'msg': verify_msg,
            'token': token,
            'vfwebqq': self.vfwebqq,
        })

    def call_server(self, api, r=None, method='post', **payloads):
        ns, api_name = api.split(':')
        conf = {
            'd': {
                'url': 'http://d.web2.qq.com/channel/{api_name}',
                'referer': 'http://d.web2.qq.com/proxy.html?v=%s&callback=1&id=1' % self.v,
                'origin': 'http://d.web2.qq.com',
            },
            's': {
                'url': 'http://s.web2.qq.com/api/{api_name}',
                'referer': 'http://s.web2.qq.com/proxy.html?v=%s&callback=1&id=1' % self.v,
                'origin': 'http://s.web2.qq.com',
            },
        }[ns]
        req = {}
        r and req.update({'r': json.dumps(r, ensure_ascii=False)})
        req.update(payloads)

        headers = {
            'Referer': conf['referer'],
            'Origin': conf['origin'],
            'User-Agent': UA_STRING,
        }

        for i in xrange(10):
            if method == 'post':
                resp = self.session.post(
                    conf['url'].format(api_name=api_name),
                    data=req, headers=headers,
                )
            elif method == 'get':
                resp = self.session.get(
                    conf['url'].format(api_name=api_name),
                    params=req, headers=headers,
                )

            if not resp.ok:
                log.error('Failed server call: %s' % resp.content)
                gevent.sleep(2 * i)
            else:
                break
        else:
            raise Exception('Max retries exceeded')

        return json.loads(resp.content)

    # ----------------

    @staticmethod
    def _plaintext(content):
        l = [i for i in content if isinstance(i, basestring)]
        return u''.join(l)

    @staticmethod
    def _buddylist_hash(qq, ptwebqq):
        a = [0] * 4
        for i, v in enumerate(ptwebqq):
            a[i % 4] ^= ord(v)

        qq = int(qq)
        d = [
            qq >> 24 & 255 ^ ord('E'),
            qq >> 16 & 255 ^ ord('C'),
            qq >> 8 & 255 ^ ord('O'),
            qq & 255 ^ ord('K'),
        ]
        j = ''.join([chr(a[s >> 1] if s % 2 == 0 else d[s >> 1]) for s in xrange(8)])
        return j.encode('hex').upper()

    @staticmethod
    def _buddylist_hash_old(qq, ptwebqq):
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

    @staticmethod
    def _buddylist_hash_nyan(qq, ptwebqq):
        b = str(qq)
        j = ptwebqq

        a = j + 'password error'
        i = ''
        while True:
            if len(i) < len(a):
                i += b
                if len(i) == len(a):
                    break
            else:
                i = i[:len(a)]
                break

        return ''.join([chr(ord(i_) ^ ord(a_)) for i_, a_ in zip(i, a)]).encode('hex').upper()


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
