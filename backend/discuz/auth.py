# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
from base64 import b64decode, b64encode
import hashlib
import time

# -- third party --
# -- own --


# -- code --
def md5(s):
    return hashlib.md5(s).hexdigest().encode('utf-8')


def _discuz_authcode(string, operation, key, expiry=0):
    assert isinstance(string, bytes)
    assert isinstance(key, bytes)
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

            string = b64decode(string[ckey_length:].decode('utf-8'))
        else:
            string = str(int(time.time()) + expiry if expiry else 10000000000)[-10:]
            string += md5(string + keyb)[:16] + string

        string_length = len(string)
        result = []

        box = list(range(256))
        rndkey = [cryptkey[i % key_length] for i in range(256)]
        j = 0
        for i in range(256):
            j = (j + box[i] + rndkey[i]) % 256
            box[i], box[j] = box[j], box[i]

        a = j = 0
        for i in range(string_length):
            a = (a + 1) % 256
            j = (j + box[a]) % 256
            box[a], box[j] = box[j], box[a]
            result.append(
                string[i] ^ (box[(box[a] + box[j]) % 256])
            )

        result = bytes(result)

        if operation == 'DECODE':
            cond = int(result[:10]) == 0 or int(result[:10]) - time.time() > 0
            cond = cond and result[10:26] == md5(result[26:] + keyb)[:16]
            if cond:
                return result[26:]
            else:
                return b''

        else:
            return keyc + b64encode(result.encode('base64')).decode('utf-8').replace('=', '')

    except Exception:
        return b''


def authencode(plain, authkey, saltkey):
    if isinstance(plain, str):
        plain = plain.encode('utf-8')
    k = (authkey + saltkey).encode('utf-8')
    return _discuz_authcode(plain, 'ENCODE', md5(k))


def authdecode(encrypted, authkey, saltkey):
    if isinstance(encrypted, str):
        encrypted = encrypted.encode('utf-8')
    k = (authkey + saltkey).encode('utf-8')
    return _discuz_authcode(encrypted, 'DECODE', md5(k))


def check_password(password, hash, salt):
    return md5(md5(password) + salt) == hash


def decode_cookie(auth, authkey, saltkey):
    rst = authdecode(auth, authkey, saltkey).decode('utf-8').split('\t')
    if not rst:
        return {}
    password, uid = rst
    return {'uid': int(uid), 'password': password}


def check_cookie_pwd(pwd, password):
    # return user.dz_member.password == password
    return pwd == password
