# -*- coding: utf-8 -*-

import logging
log = logging.getLogger('user_settings')

from utils import instantiate
import simplejson as json
import os.path

import atexit

from collections import namedtuple
Category = namedtuple('Category', ['description', 'settings'])


class UserSettings(dict): 
    def __init__(self):
        self.categories = { }
        self.add_category(None)
        self.add_settings(saves = { })

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, v):
        self[name] = v

    def add_category(self, name, desc = ''):
        self.categories[name] = Category(desc, set())

    def add_setting(self, name, default = None, category = None):
        if name not in self:
            self[name] = default
        
        self.categories[category].settings.add(name)

    def add_settings(self, category = None, **defaults):
        for name, default in defaults.iteritems():
            self.add_setting(name, default, category)

    def save_category(self, category, value):
        if category not in self.categories:
            raise KeyError
        
        if value:
            self.saves[category] = True
        else:
            try:
                del self.saves[category]
            except KeyError:
                pass

    def save(self):
        cat = self.categories
        names = set.union(
            cat[None].settings, 
            *(cat[c].settings for c in self.saves)
        )
        with open(self._get_conf_name(), 'w') as f:
            f.write(json.dumps({ k: self[k] for k in names }))

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

UserSettings.add_settings(last_id = u'无名の罪袋', saved_pass = '')

UserSettings.load()
atexit.register(UserSettings.save)
