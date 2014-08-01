# -*- coding: utf-8 -*-

from gamepack.thb import params
from .common import gen_metafunc

__metaclass__ = gen_metafunc(params)


class RandomSeat:
    description = u'随机座位'

    options = (
        (u'启用', True),
        (u'禁用', False),
    )


class NoImbaCharacters:
    description = u'不平衡角色'

    options = (
        (u'允许', False),
        (u'禁止', True),
    )
