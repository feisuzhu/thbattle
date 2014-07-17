# -*- coding: utf-8 -*-

from utils import DataHolder
from .resource import resource as cres

# -----BEGIN BADGES UI META-----
badges = {}


def badge_metafunc(clsname, bases, _dict):
    data = DataHolder.parse(_dict)
    badges[clsname] = data

__metaclass__ = badge_metafunc


class dev:
    badge_anim = cres.badges.dev
    badge_text = u'符斗祭程序开发组成员'

# -----END BADGES UI META-----
