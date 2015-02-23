# -*- coding: utf-8 -*-

# -- stdlib --
from base64 import b64encode, b64decode
from functools import wraps
import argparse
import hashlib
import logging
import sys
import time

# -- third party --
from gevent.server import StreamServer
from sqlalchemy import Column, Integer, String, Float, Index, DateTime
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session


# -- own --
from utils.rpc import RPCService


# -- globals --
CREDITS_MAPPING = {
    'credits': 'extcredits2',
    'games': 'extcredits8',
    'drops': 'extcredits7',
}


# -- code --
Model = declarative_base()

options = None
session = None


class Badges(Model):
    __tablename__ = 'thb_badges'

    id    = Column(Integer, primary_key=True)
    uid   = Column(Integer, nullable=False)
    badge = Column(String(32), nullable=False)


class PeerRating(Model):
    __tablename__ = 'thb_peer_rating'

    id   = Column(Integer, primary_key=True)
    gid  = Column(Integer, nullable=False)    # game id
    uid1 = Column(Integer, nullable=False)    # user 1 (thinks)
    uid2 = Column(Integer, nullable=False)    # user 2
    vote = Column(Integer, nullable=False)    # played (well -> 1, sucks -> -1)

    __table_args__ = (
        Index('peer_rating_uniq', 'gid', 'uid1', 'uid2', unique=True),
    )


class PlayerRank(Model):
    # computed from PeerRating, using PageRank.
    __tablename__ = 'thb_player_rank'
    uid   = Column(Integer, primary_key=True)
    score = Column(Float, nullable=False)


class GameResult(Model):
    __tablename__ = 'thb_game_result'
    gid     = Column(Integer, primary_key=True)
    mode    = Column(String(20), nullable=False)  # 'THBattleFaith'
    players = Column(String(120), nullable=False)  # '2,123,43534,1231,345,144'
    winner  = Column(String(60), nullable=False)  # '2,123,144'
    time    = Column(DateTime(True), nullable=False)  # datetime.isoformat()


# other things: game items, hidden character availability, etc.

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


class MemberService(RPCService):
    def clear_session(f):
        @wraps(f)
        def wrapper(*a, **k):
            try:
                return f(*a, **k)
            finally:
                session.rollback()
                session.remove()

        wrapper.__name__ = f.__name__
        return wrapper

    @clear_session
    def get_user_info(self, uid):
        uid = int(uid)

        member = session.execute(text('''
            SELECT * FROM pre_common_member
            WHERE uid=:uid
        '''), {'uid': int(uid)}).fetchone()

        if not member:
            return {}

        return self._get_user_info(member)

    @clear_session
    def get_user_info_by_username(self, username):
        if isinstance(username, unicode):
            username = username.encode('utf-8')

        member = session.execute(text('''
            SELECT * FROM pre_common_member
            WHERE username=:username
        '''), {'username': username}).fetchone()

        if not member:
            return {}

        return self._get_user_info(member)

    def _get_user_info(self, member):
        uid = member.uid

        ucmember = session.execute(text('''
            SELECT * FROM pre_ucenter_members
            WHERE uid=:uid
        '''), {'uid': int(uid)}).fetchone()

        mcount = session.execute(text('''
            SELECT * FROM pre_common_member_count
            WHERE uid=:uid
        '''), {'uid': int(uid)}).fetchone()

        mfield = session.execute(text('''
            SELECT * FROM pre_common_member_field_forum
            WHERE uid=:uid
        '''), {'uid': int(uid)}).fetchone()

        badges = session.query(Badges.badge) \
            .filter_by(uid=int(uid)) \
            .order_by(Badges.id.desc()) \
            .all()

        badges = [i for i, in badges]

        rst = {
            'uid': int(uid),
            'username': member.username,
            'password': member.password,
            'ucpassword': ucmember.password,
            'ucsalt': ucmember.salt,
            'status': member.status,
            'title': mfield.customstatus,
            'badges': badges,
        }

        for k, v in CREDITS_MAPPING.items():
            rst[k] = getattr(mcount, v)

        return rst

    @clear_session
    def validate_by_uid(self, uid, password):
        info = self.get_user_info(uid)

        if not info:
            return {}

        if isinstance(password, unicode):
            password = password.encode('utf-8')

        if md5(md5(password) + info['ucsalt']) != info['ucpassword']:
            return {}

        return info

    @clear_session
    def validate_by_username(self, username, password):
        if isinstance(password, unicode):
            password = password.encode('utf-8')

        member = self.get_user_info_by_username(username)

        if not member:
            return {}

        info = self.get_user_info(member['uid'])

        if md5(md5(password) + info['ucsalt']) != info['ucpassword']:
            return {}

        return info

    @clear_session
    def validate_by_cookie(self, auth, saltkey):
        rst = authdecode(auth, saltkey)
        if not rst:
            return {}

        password, uid = rst.split('\t')

        info = self.get_user_info(int(uid))

        if not info or password != info['password']:
            return {}

        return info

    @clear_session
    def add_credit(self, uid, type, amount):
        field = CREDITS_MAPPING.get(type)
        if not type:
            return {}

        # be aware of sql injection
        session.execute(text('''
            UPDATE pre_common_member_count
            SET %s = %s + :amount
            WHERE uid=:uid
        ''' % (field, field)), {'amount': int(amount), 'uid': int(uid)})

        return self.get_user_info(uid)

    del clear_session


def main():
    global options, session
    parser = argparse.ArgumentParser(sys.argv[0])
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=7000)
    parser.add_argument('--connect-str', default='mysql://root@localhost/ultrax?charset=utf8')
    parser.add_argument('--discuz-authkey', default='Proton rocks')
    parser.add_argument('--log', default='ERROR')
    options = parser.parse_args()

    logging.basicConfig(level=options.log.upper())

    engine = create_engine(
        options.connect_str,
        encoding='utf-8',
        convert_unicode=True,
    )
    Model.metadata.create_all(engine)

    session = scoped_session(sessionmaker(bind=engine))

    server = StreamServer((options.host, options.port), MemberService.spawn, None)
    server.serve_forever()


if __name__ == '__main__':
    main()
