# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from .common import G
from gamepack.thb import cards
from utils import ObjectDict

# -----BEGIN TAGS UI META-----
tags = {}


def tag_metafunc(clsname, bases, _dict):
    _dict.pop('__module__')
    data = ObjectDict.parse(_dict)
    tags[clsname] = data

__metaclass__ = tag_metafunc


class attack_num:
    tag_anim = lambda p: 'thb-tag-attacked'

    def display(p, v):
        if cards.AttackCardHandler.is_freeattack(p):
            return False

        return v <= 0 and G().current_player is p

    description = u'该玩家在此回合不能再使用【弹幕】了'


class wine:
    tag_anim = lambda p: 'thb-tag-wine'
    display = lambda p, v: v
    description = u'喝醉了…'


class flan_cs:
    tag_anim = lambda p: 'thb-tag-flandrecs'
    display = lambda p, v: v >= p.tags['turn_count'] and G().current_player is p
    description = u'玩坏你哦！'


class lunadial:
    tag_anim = lambda p: 'thb-tag-lunadial'
    display = lambda p, v: v and G().current_player is p
    description = u'咲夜的时间！'


class books:
    def tag_anim(p):
        n = min(p.tags['books'], 6)
        return 'thb-tag-books@0%d' % n

    display = lambda p, v: v
    description = u'书的数量'


class riverside_target:
    tag_anim = lambda p: 'thb-tag-riverside'
    display = lambda p, v: v == G().turn_count
    description = u'被指定为彼岸的目标'


class ran_ei:
    tag_anim = lambda p: 'thb-tag-ran_ei'
    display = lambda p, v: v < p.tags['turn_count'] + 1
    description = u'还可以发动【极智】'


class aya_count:
    tag_anim = lambda p: 'thb-tag-aya_range_max'
    display = lambda p, v: v >= 2 and p is G().current_player
    description = u'使用卡牌时不受距离限制'


class exterminate:
    tag_anim = lambda p: 'thb-tag-flandre_exterminate'
    display = lambda p, v: v
    description = u'毁灭：无法使用人物技能'


class reisen_discarder:
    tag_anim = lambda p: 'thb-tag-reisen_discarder'
    display = lambda p, v: v
    description = u'丧心：下一个出牌阶段只能使用弹幕，且只能对最近的角色使用弹幕'


class shizuha_decay:
    tag_anim = lambda p: 'thb-tag-shizuha_decay'
    display = lambda p, v: v
    description = u'凋零：弃牌阶段需额外弃置一张手牌'

# -----END TAGS UI META-----
