# -*- coding: utf-8 -*-

import hashlib
import argparse
from utils.crypto import aes_encrypt

parser = argparse.ArgumentParser('encrypt')
parser.add_argument('filename')
parser.add_argument('passphrase')
options = parser.parse_args()

fn = options.filename
if fn.endswith('.png'):
    fn = fn[:-4]

data = open(options.filename, 'rb').read()
key = hashlib.sha256(options.passphrase).digest()
hint = hashlib.sha256(key).digest().encode('base64')

enc = aes_encrypt(data, key)
open(fn + '_encrypted.bin', 'wb').write(enc)
open(fn + '.hint', 'wb').write(hint)
