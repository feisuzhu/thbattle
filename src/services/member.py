# -*- coding: utf-8 -*-

# -- stdlib --
import sys
import argparse
import hashlib
import time
from base64 import b64encode, b64decode
from functools import partial

# -- third party --
from sqlalchemy import create_engine, text as sq_text
from gevent.server import StreamServer

# -- own --
from utils.rpc import RPCService


# -- globals --
CREDITS_MAPPING = {
    'credits': 'extcredits2',
    'games': 'extcredits8',
    'drops': 'extcredits7',
}


# -- code --
parser = argparse.ArgumentParser(sys.argv[0])
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=7000)
parser.add_argument('--connect-str', default='mysql://root@localhost/ultrax?charset=utf8')
parser.add_argument('--discuz-dbpre', default='pre_')
parser.add_argument('--discuz-authkey', default='Proton rocks')
options = parser.parse_args()

engine = create_engine(
    options.connect_str,
    encoding='utf-8',
    convert_unicode=True,
)

text = lambda t: sq_text(t.replace('cdb_', options.discuz_dbpre))


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


class MemberService(RPCService):
    def get_user_info(self, uid):
        member = engine.execute(text('''
            SELECT * FROM cdb_common_member
            WHERE uid=:uid
        '''), uid=int(uid)).fetchone()

        if not member:
            return {}

        ucmember = engine.execute(text('''
            SELECT * FROM cdb_ucenter_members
            WHERE uid=:uid
        '''), uid=uid).fetchone()

        mcount = engine.execute(text('''
            SELECT * FROM cdb_common_member_count
            WHERE uid=:uid
        '''), uid=int(uid)).fetchone()

        mfield= engine.execute(text('''
            SELECT * FROM cdb_common_member_field_forum
            WHERE uid=:uid
        '''), uid=int(uid)).fetchone()

        rst = {
            'uid': int(uid),
            'username': member.username,
            'password': member.password,
            'ucpassword': ucmember.password,
            'ucsalt': ucmember.salt,
            'status': member.status,
            'title': mfield.customstatus,
        }

        for k, v in CREDITS_MAPPING.items():
            rst[k] = getattr(mcount, v)

        return rst

    def validate_by_uid(self, uid, password):
        info = self.get_user_info(uid)

        if not info:
            return {}

        if md5(md5(password.encode('utf-8')) + info['ucsalt']) != info['ucpassword']:
            return {}

        return info

    def validate_by_username(self, username, password):
        ucmember = engine.execute(text('''
            select * from cdb_ucenter_members
            where username=:username
        '''), username=username).fetchone()

        if not ucmember:
            return {}

        info = self.get_user_info(ucmember.uid)

        if md5(md5(password.encode('utf-8')) + info['ucsalt']) != info['ucpassword']:
            return {}

        return info

    def validate_by_cookie(self, auth, saltkey):
        rst = authdecode(auth, saltkey)
        if not rst:
            return {}

        password, uid = rst.split('\t')

        info = self.get_user_info(int(uid))

        if not info or password != info['password']:
            return {}

        return info

    def add_credit(self, uid, type, amount):
        field = CREDITS_MAPPING.get(type)
        if not type:
            return {}

        # be aware of sql injection
        engine.execute(text('''
            UPDATE cdb_common_member_count
            SET %s = %s + :amount
            WHERE uid=:uid
        ''' % (field, field)), amount=amount, uid=uid)

        return self.get_user_info(uid)


server = StreamServer((options.host, options.port), MemberService.spawn, None)
server.serve_forever()
