# -*- coding: utf-8 -*-

from utils import ObjectDict
from .resource import resource as cres

# -----BEGIN BADGES UI META-----
badges = {}


def badge_metafunc(clsname, bases, _dict):
    _dict.pop('__module__')
    data = ObjectDict.parse(_dict)
    badges[clsname] = data

__metaclass__ = badge_metafunc


class dev:
    badge_anim = cres.badges.dev
    badge_text = u'符斗祭程序开发组成员'

# -----END BADGES UI META-----
