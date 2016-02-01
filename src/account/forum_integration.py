# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
import logging

# -- third party --
import gevent

# -- own --
from account.base import AccountBase, server_side_only
from utils import log_failure
from server.db.session import Session
from server.db.models import DiscuzMember, User
import itertools
from sqlalchemy import func


# -- code --
try_counter = itertools.count(10032).next
log = logging.getLogger('forum_integration')


def md5(s):
    return hashlib.md5(s).hexdigest()


def _discuz_authcode(string, operation, key, expiry=0):
    try:
        ckey_length = 4
        key = md5(key)
        keya = md5(key[:16])
        keyb = md5(key[16:])
        if ckey_length:
            if operation == 'DECODE':
                keyc = string[:ckey_length]
            else:
                keyc = md5(str(time.time()))[-ckey_length:]
        else:
            keyc = ''

        cryptkey = keya + md5(keya + keyc)
        key_length = len(cryptkey)

        if operation == 'DECODE':
            pads = len(string) % 4 - 4
            if pads != -4:
                string += '=' * -pads

            string = b64decode(string[ckey_length:])
        else:
            string = str(int(time.time()) + expiry if expiry else 10000000000)[-10:]
            string += md5(string + keyb)[:16] + string

        string_length = len(string)
        result = []

        box = range(256)
        rndkey = [ord(cryptkey[i % key_length]) for i in xrange(256)]
        j = 0
        for i in xrange(256):
            j = (j + box[i] + rndkey[i]) % 256
            box[i], box[j] = box[j], box[i]

        a = j = 0
        for i in xrange(string_length):
            a = (a + 1) % 256
            j = (j + box[a]) % 256
            box[a], box[j] = box[j], box[a]
            result.append(
                chr(ord(string[i]) ^ (box[(box[a] + box[j]) % 256]))
            )

        result = ''.join(result)

        if operation == 'DECODE':
            cond = int(result[:10]) == 0 or int(result[:10]) - time.time() > 0
            cond = cond and result[10:26] == md5(result[26:] + keyb)[:16]
            if cond:
                return result[26:]
            else:
                return ''

        else:
            return keyc + b64encode(result).replace('=', '')

    except:
        return ''


def authencode(plain, saltkey):
    return _discuz_authcode(plain, 'ENCODE', md5(options.discuz_authkey + saltkey))


def authdecode(encrypted, saltkey):
    return _discuz_authcode(encrypted, 'DECODE', md5(options.discuz_authkey + saltkey))


class Account(AccountBase):
    is_guest = False

    @classmethod
    @server_side_only
    def authenticate(cls, username, password):
        try:
            s = Session()

            try:
                uid = int(username)
                uid = uid if uid < 500000 else None
            except ValueError:
                uid = None

            if uid == -1:
                acc = cls()
                acc._fill_trygame()
                return acc
            elif uid:
                dz_member = s.query(DiscuzMember).filter(DiscuzMember.uid == uid).first()
            else:
                dz_member = s.query(DiscuzMember).filter(DiscuzMember.email == username).first()
                dz_member = dz_member or s.query(DiscuzMember).filter(DiscuzMember.username == username).first()

            if not dz_member:
                return False

            acc = cls()
            acc._fill_account(dz_member)

            dz_member.member_status.lastactivity = func.unix_timestamp()

            s.commit()

            return acc
        except:
            s.rollback()
            raise

    @server_side_only
    def refresh(self):
        try:
            s = Session()
            dz_member = s.query(DiscuzMember).filter(DiscuzMember.uid == self.userid).first()
            dz_member and self._fill_account(dz_member)
            s.commit()
        except:
            s.rollback()
            raise

    @server_side_only
    def _fill_account(self, data):
        self.username = data['username'].decode('utf-8')
        self.status = data['status']
        self.userid = data['uid']

        from urlparse import urljoin
        from settings import ACCOUNT_FORUMURL

        self.other = defaultdict(
            lambda: None,
            title=data['title'].decode('utf-8'),
            avatar=urljoin(
                ACCOUNT_FORUMURL,
                '/uc_server/avatar.php?uid=%d&size=middle' % data['uid'],
            ),
            credits=data['credits'],
            games=data['games'],
            drops=data['drops'],
            badges=data['badges'],
        )

    @server_side_only
    def _fill_trygame(self):
        self.username = u'毛玉' + str(c)
        self.status = 0
        self.userid = -try_counter()

        from urlparse import urljoin
        from settings import ACCOUNT_FORUMURL

        self.other = defaultdict(
            lambda: None,
            title=u'不愿注册的毛玉',
            avatar=urljoin(
                ACCOUNT_FORUMURL,
                '/maoyu.png'
            ),
            credits=-998,
            games=0,
            drops=0,
            badges=[],
        )

    @server_side_only
    def available(self):
        return self.status != -1

    @server_side_only
    def add_credit(self, type, amount):
        if self.userid < 0:
            return

        @gevent.spawn
        @log_failure(log)
        def worker():
            with clipool() as cli:
                rst = cli.add_credit(self.userid, type, amount)
                rst and self._fill_account(rst)

    @server_side_only
    def is_maoyu(self):
        return self.userid < 0
