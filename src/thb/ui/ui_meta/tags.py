# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import itertools

# -- third party --
# -- own --
from .common import G
from utils import ObjectDict


# -- code --
# -----BEGIN TAGS UI META-----
tags = {}


def tag_metafunc(clsname, bases, _dict):
    _dict.pop('__module__')
    data = ObjectDict.parse(_dict)
    tags[clsname] = data

__metaclass__ = tag_metafunc


def get_display_tags(p):
    from thb.actions import ttags

    rst = []

    try:
        for t, v in itertools.chain(p.tags.items(), ttags(p).items()):
            meta = tags.get(t)
            if not meta:
                continue

            anim = meta.anim(p, v)
            if not anim:
                continue

            desc = meta.description(p, v)

            rst.append((anim, desc))

        for c in list(getattr(p, 'fatetell', ())):
            rst.append((c.ui_meta.tag_anim(c), c.ui_meta.description))

    except AttributeError:
        pass

    return rst


class vitality:
    def anim(p, v):
        if v <= 0 and G().current_player is p:
            return 'thb-tag-attacked'

    def description(p, v):
        return '没有干劲了……'


class wine:
    def anim(p, v):
        return v and 'thb-tag-wine'

    def description(p, v):
        return '喝醉了…'


class flan_cs:
    def anim(p, v):
        if v >= p.tags['turn_count'] and G().current_player is p:
            return 'thb-tag-flandrecs'

    def description(p, v):
        return '玩坏你哦！'


class lunadial:
    def anim(p, v):
        if v and G().current_player is p:
            return 'thb-tag-lunadial'

    def description(p, v):
        return '咲夜的时间！'


class books:
    def anim(p, v):
        n = min(v, 6)
        return 'thb-tag-books@0%d' % n

    def description(p, v):
        return '书的数量'


class riverside_target:
    def anim(p, v):
        if v == G().turn_count:
            return 'thb-tag-riverside'

    def description(p, v):
        return '被指定为彼岸的目标'


class ran_ei:
    def anim(p, v):
        if v < p.tags['turn_count'] + 1:
            return 'thb-tag-ran_ei'

    def description(p, v):
        return '还可以发动极智'


class aya_count:
    def anim(p, v):
        if v >= 2 and p is G().current_player:
            return 'thb-tag-aya_range_max'

    def description(p, v):
        return '使用卡牌时不受距离限制'


class exterminate:
    def anim(p, v):
        return v and 'thb-tag-flandre_exterminate'

    def description(p, v):
        return '毁灭：无法使用人物技能'


class reisen_discarder:
    def anim(p, v):
        return v and 'thb-tag-reisen_discarder'

    def description(p, v):
        return '丧心：下一个出牌阶段只能使用弹幕，且只能对最近的角色使用弹幕'


class shizuha_decay:
    def anim(p, v):
        return v and 'thb-tag-shizuha_decay'

    def description(p, v):
        return '凋零：弃牌阶段需额外弃置一张手牌'


class dominance_suit_SPADE:
    def anim(p, v):
        if v and p is G().current_player:
            return 'thb-tag-suit_spade'

    def description(p, v):
        return '风靡：使用过♠牌'


class dominance_suit_HEART:
    def anim(p, v):
        if v and p is G().current_player:
            return 'thb-tag-suit_heart'

    def description(p, v):
        return '风靡：使用过♥牌'


class dominance_suit_DIAMOND:
    def anim(p, v):
        if v and p is G().current_player:
            return 'thb-tag-suit_diamond'

    def description(p, v):
        return '风靡：使用过♦牌'


class dominance_suit_CLUB:
    def anim(p, v):
        if v and p is G().current_player:
            return 'thb-tag-suit_club'

    def description(p, v):
        return '风靡：使用过♣牌'


class scarlet_mist:
    def anim(p, v):
        if v == 'buff':
            return 'thb-tag-scarlet_mist'

    def description(p, v):
        return '红雾：增益效果'


class keine_devour:
    def anim(p, v):
        if v and p is G().current_player:
            return 'thb-tag-keine_devour'

    def description(p, v):
        return '这位玩家的历史将会被慧音吞噬'

# -----END TAGS UI META-----
