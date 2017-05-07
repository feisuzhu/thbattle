# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict
import hashlib
import itertools
import logging
import time

# -- third party --
# -- own --
import gevent
from account.base import AccountBase, server_side_only
from utils import password_hash
from db import transactional, current_session
from utils import log_failure
from db import transactional


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

            string = string[ckey_length:].decode('base64')
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
            return keyc + result.encode('base64').replace('=', '')

    except:
        return ''


def authencode(plain, saltkey):
    from options import options
    return _discuz_authcode(plain, 'ENCODE', md5(options.discuz_authkey + saltkey))


def authdecode(encrypted, saltkey):
    from options import options
    return _discuz_authcode(encrypted, 'DECODE', md5(options.discuz_authkey + saltkey))


class Account(AccountBase):
    is_guest = False

    @classmethod
    @server_side_only
    @transactional()
    def authenticate(cls, username, password, session=None):
        from sqlalchemy import func
        try:
            if int(username) == -1:
                acc = cls()
                acc._fill_trygame()
                return acc
        except:
            pass

        user = cls.find(username)

        if not user:
            return False

        if not cls.validate_by_password(user, password):
            return False

        # sync
        dz_member = user.dz_member
        user.id       = dz_member.uid
        user.username = dz_member.username
        user.password = password_hash(password)
        user.email    = dz_member.email
        user.title    = dz_member.member_field.customstatus
        user.status   = dz_member.status

        acc = cls()
        acc._fill_account(user)

        user.lastactivity = func.unix_timestamp()
        dz_member.member_status.lastactivity = func.unix_timestamp()

        return acc

    @staticmethod
    @server_side_only
    @transactional()
    def find(id):
        from db.models import DiscuzMember, User
        from sqlalchemy.orm import joinedload

        s = current_session()

        try:
            uid = int(id)
            uid = uid if uid < 500000 else None
        except ValueError:
            uid = None

        q = s.query(DiscuzMember).options(joinedload('ucmember'))
        if uid:
            dz_member = q.filter(DiscuzMember.uid == uid).first()
        else:
            dz_member = q.filter(DiscuzMember.email == id).first()
            dz_member = dz_member or q.filter(DiscuzMember.username == id).first()

        if not dz_member:
            return None

        uid = dz_member.uid
        user = s.query(User).filter(User.id == uid).first()
        if not user:
            user = User()
            s.add(user)

        user.dz_member = dz_member

        # sync
        user.games    = dz_member.member_count.games
        user.drops    = dz_member.member_count.drops
        user.jiecao   = dz_member.member_count.jiecao

        return user

    @server_side_only
    @transactional()
    def refresh(self):
        user = self.find(self.userid)
        user and self._fill_account(user)

    @server_side_only
    def _fill_account(self, user):
        self.username = user.username
        self.status = user.status
        self.userid = user.id

        from urlparse import urljoin
        from settings import ACCOUNT_FORUMURL

        self.other = defaultdict(
            lambda: None,
            title=user.title,
            avatar=urljoin(
                ACCOUNT_FORUMURL,
                '/uc_server/avatar.php?uid=%d&size=middle' % user.id,
            ),
            credits=user.jiecao,
            games=user.games,
            drops=user.drops,
        )

    @server_side_only
    def _fill_trygame(self):
        c = try_counter()
        self.username = u'毛玉' + str(c)
        self.status = 0
        self.userid = -c

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
        )

    @server_side_only
    def available(self):
        return self.status != -1

    @classmethod
    @server_side_only
    @transactional()
    def add_user_credit(cls, user, lst, negcheck=None):
        try:
            member_count = user.dz_member.member_count
        except AttributeError:
            user = cls.find(user.id)
            member_count = user.dz_member.member_count

        for type, amount in lst:
            if type in ('jiecao', 'games', 'drops'):
                total = getattr(member_count, type) + amount
                if negcheck and total < 0:
                    raise negcheck

                setattr(member_count, type, total)

        for type, amount in lst:
            if type in ('jiecao', 'games', 'drops', 'ppoint'):
                total = getattr(user, type) + amount
                if negcheck and total < 0:
                    raise negcheck

                setattr(user, type, total)

    @server_side_only
    def add_credit(self, lst):
        if self.is_maoyu() < 0:
            return

        @gevent.spawn
        @log_failure(log)
        @transactional()
        def worker():
            uid = self.userid
            user = self.find(uid)
            self.add_user_credit(user, lst)
            self.refresh()

    @server_side_only
    def is_maoyu(self):
        return self.userid < 0

    @staticmethod
    @server_side_only
    def validate_by_password(user, password):
        dz_member = user.dz_member
        if isinstance(password, unicode):
            password = password.encode('utf-8')

        return md5(md5(password) + dz_member.ucmember.salt) == dz_member.ucmember.password

    @staticmethod
    def decode_cookie(auth, saltkey):
        password, uid = authdecode(auth, saltkey).split('\t')
        return uid, password

    @staticmethod
    @server_side_only
    def validate_by_cookie_pwd(user, password):
        return user.dz_member.password == password
