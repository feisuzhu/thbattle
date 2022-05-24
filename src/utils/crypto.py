# -*- coding: utf-8 -*-

# -- stdlib --
from cStringIO import StringIO
import hashlib
import os

# -- third party --
# -- own --
# -- code --
IV = 'The init vector.'


# def _aes_op(data, key, op):
#     assert len(key) == 32  # 256 bits

#     buf = StringIO()
#     import M2Crypto
#     c = M2Crypto.EVP.Cipher('aes_256_cbc', key, IV, op)

#     buf.write(c.update(data))
#     buf.write(c.final())
#     return buf.getvalue()


# def aes_encrypt(data, key):
#     return _aes_op(data, key, 1)


# def aes_decrypt(data, key):
#     return _aes_op(data, key, 0)


def simple_encrypt(data):
    return data


def simple_decrypt(data):
    return data


# not using [sb]crypt, this is good enough, not adding dependency

def password_hash(pwd):
    pwd = pwd.encode('utf-8') if isinstance(pwd, unicode) else pwd
    salt = os.urandom(7)
    return (hashlib.sha256(salt + pwd + salt).digest() + salt).encode('base64').strip()


def password_hash_verify(pwd, hash):
    raw = hash.decode('base64')
    pwd = pwd.encode('utf-8') if isinstance(pwd, unicode) else pwd
    hash, salt = raw[:32], raw[32:]
    return hashlib.sha256(salt + pwd + salt).digest() == hash
