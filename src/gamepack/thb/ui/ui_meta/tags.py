# -*- coding: utf-8 -*-

from gamepack.thb.ui.resource import resource as gres
from gamepack.thb import cards

from .common import G
from utils import DataHolder

# -----BEGIN TAGS UI META-----
tags = {}


def tag_metafunc(clsname, bases, _dict):
    data = DataHolder.parse(_dict)
    tags[clsname] = data

__metaclass__ = tag_metafunc


class attack_num:
    tag_anim = lambda p: gres.tag_attacked

    def display(p, v):
        if cards.AttackCardHandler.is_freeattack(p):
            return False

        return v <= 0 and G().current_turn is p

    description = u'该玩家在此回合不能再使用【弹幕】了'


class wine:
    tag_anim = lambda p: gres.tag_wine
    display = lambda p, v: v
    description = u'喝醉了…'


class flan_cs:
    tag_anim = lambda p: gres.tag_flandrecs
    display = lambda p, v: v >= p.tags['turn_count'] and G().current_turn is p
    description = u'玩坏你哦！'


class lunaclock:
    tag_anim = lambda p: gres.tag_lunaclock
    display = lambda p, v: v and G().current_turn is p
    description = u'咲夜的时间！'


class faithcounter:
    def tag_anim(p):
        n = min(len(p.faiths), 6)
        return gres.tag_faiths[n]

    display = lambda p, v: v
    description = u'信仰数'


class action:
    tag_anim = lambda p: gres.tag_action
    display = lambda p, v: v
    description = u'可以行动'


class riverside_target:
    tag_anim = lambda p: gres.tag_riverside
    display = lambda p, v: v
    description = u'被指定为彼岸的目标'


class ran_ei:
    tag_anim = lambda p: gres.tag_ran_ei
    display = lambda p, v: v < p.tags['turn_count'] + 1
    description = u'还可以发动【极智】'


class divinity_target:
    tag_anim = lambda p: gres.tag_action
    display = lambda p, v: v
    description = u'被神威震慑的动弹不得'

# -----END TAGS UI META-----
