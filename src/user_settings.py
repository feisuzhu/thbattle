# -*- coding: utf-8 -*-

import logging
log = logging.getLogger('user_settings')

from utils import instantiate
import simplejson as json
import os.path

import atexit


class UserSettings(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, v):
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

        except Exception as e:
            log.exception(e)

    def _get_conf_name(self):
        import settings
        return os.path.join(settings.UPDATE_BASE, 'user_settings.json')


UserSettings = UserSettings()

UserSettings.add_setting('last_id', u'无名の罪袋')
UserSettings.add_setting('notify_level', 1)

UserSettings.load()
atexit.register(UserSettings.save)
