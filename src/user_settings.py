# -*- coding: utf-8 -*-

from utils.misc import Observable 
from utils.crypto import aes_encrypt, aes_decrypt
import hashlib
import atexit
import logging
import os.path
import simplejson as json

log = logging.getLogger('user_settings')

_crypto_key = hashlib.sha256('zheshijintiandeqiaokelijianpan').digest()
_enc_head = 'ENC_HEAD'

class UserSettings(dict, Observable):
    __slots__ = ('_ob_dict', '_enc')

    def __setitem__(self, k, v):
        dict.__setitem__(self, k, v)
        self.notify('setting_change', k, v)

    def __getattr__(self, name):
        try:
            v = self[name]
            if name in self._enc:
                try:
                    v = aes_decrypt(v.decode('base64'), _crypto_key)
                except:
                    return ''
                
                v = v[8:] if v.startswith(_enc_head) else ''

            return v

        except KeyError:
            raise AttributeError

    def __init__(self):
        super(type(self), self).__init__()
        self._enc = set()

    def __setattr__(self, name, v):
        if name.startswith('_'):
            dict.__setattr__(self, name, v)
            return 
        
        if name in self._enc:
            v = aes_encrypt(_enc_head + str(v), _crypto_key).encode('base64')

        self[name] = v

    def add_setting(self, name, default, encrypted=False):
        if encrypted:
            self._enc.add(name)

        setattr(self, name, default)

    def save(self):
        with open(self._get_conf_name(), 'w') as f:
            f.write(json.dumps(self))

    def load(self):
        conf = self._get_conf_name()
        if not os.path.exists(conf):
            return

        try:
            with open(conf, 'r') as f:
                self.update(json.loads(f.read()))

        except:
            log.exception('Error loading conf')

    def _get_conf_name(self):
        import settings
        return os.path.join(settings.UPDATE_BASE, 'user_settings.json')


UserSettings = UserSettings()

UserSettings.add_setting('last_id', u'无名の罪袋')
UserSettings.add_setting('saved_passwd', '', encrypted=True)
UserSettings.add_setting('notify_level', 1)
UserSettings.add_setting('sound_notify', True)
UserSettings.add_setting('volume', 1.0)

UserSettings.load()

# reset at start
UserSettings.no_invite = False

atexit.register(UserSettings.save)
