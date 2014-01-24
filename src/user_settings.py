# -*- coding: utf-8 -*-

from weakref import WeakSet
import atexit
import logging
import os.path
import simplejson as json

log = logging.getLogger('user_settings')


class UserSettings(dict):
    __slots__ = ()

    def __init__(self):
        dict.__init__(self)
        self['__observers__'] = WeakSet()

    def __setitem__(self, k, v):
        dict.__setitem__(self, k, v)
        for ob in self['__observers__']:
            ob(k, v)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, v):
        self[name] = v

    def add_setting(self, name, default):
        self[name] = default

    def add_observer(self, ob):
        self['__observers__'].add(ob)

    def save(self):
        with open(self._get_conf_name(), 'w') as f:
            d = dict(self)
            d.pop('__observers__')
            f.write(json.dumps(d))

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
UserSettings.add_setting('notify_level', 1)
UserSettings.add_setting('sound_notify', True)
UserSettings.add_setting('volume', 1.0)

UserSettings.load()

# reset at start
UserSettings.add_setting('no_invite', False)

atexit.register(UserSettings.save)
