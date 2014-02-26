# -*- coding: utf-8 -*-

from utils.misc import Observable
from utils.crypto import simple_encrypt
import atexit
import logging
import os.path
import simplejson as json

log = logging.getLogger('user_settings')


class UserSettings(dict, Observable):
    __slots__ = ('_ob_dict', )

    def __setitem__(self, k, v):
        dict.__setitem__(self, k, v)
        self.notify('setting_change', k, v)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, v):
        if name.startswith('_'):
            dict.__setattr__(self, name, v)
            return

        self[name] = v

    def add_setting(self, name, default):
        self[name] = default

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
UserSettings.add_setting('saved_passwd', simple_encrypt(''))
UserSettings.add_setting('notify_level', 1)
UserSettings.add_setting('sound_notify', True)
UserSettings.add_setting('volume', 1.0)

UserSettings.load()

# reset at start
UserSettings.no_invite = False

atexit.register(UserSettings.save)
