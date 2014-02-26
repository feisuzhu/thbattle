# -*- coding: utf-8 -*-

from cStringIO import StringIO

IV = 'The init vector.'


def _aes_op(data, key, op):
    assert len(key) == 32  # 256 bits

    buf = StringIO()
    import M2Crypto
    c = M2Crypto.EVP.Cipher('aes_256_cbc', key, IV, op)

    buf.write(c.update(data))
    buf.write(c.final())
    return buf.getvalue()


def aes_encrypt(data, key):
    return _aes_op(data, key, 1)


def aes_decrypt(data, key):
    return _aes_op(data, key, 0)

import hashlib
_simple_key = hashlib.sha256('zheshijintiandeqiaokelijianpan').digest()
_enc_head = 'ENC_HEAD'

def simple_encrypt(data):
    return aes_encrypt(_enc_head + str(data), _simple_key).encode('base64')

def simple_decrypt(data):
    try:
        v = aes_decrypt(data.decode('base64'), _simple_key)
        assert v.startswith(_enc_head)
        return v[len(_enc_head):]
    except:
        return ''
