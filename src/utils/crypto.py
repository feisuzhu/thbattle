# -*- coding: utf-8 -*-

import M2Crypto
from cStringIO import StringIO

IV = 'The init vector.'


def _aes_op(data, key, op):
    assert len(key) == 32  # 256 bits

    buf = StringIO()
    c = M2Crypto.EVP.Cipher('aes_256_cbc', key, IV, op)

    buf.write(c.update(data))
    buf.write(c.final())
    return buf.getvalue()


def aes_encrypt(data, key):
    return _aes_op(data, key, 1)


def aes_decrypt(data, key):
    return _aes_op(data, key, 0)
