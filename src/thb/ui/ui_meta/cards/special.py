# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import cards
from thb.ui.ui_meta.common import gen_metafunc


# -- code --
__metaclass__ = gen_metafunc(cards)


class PPointCard:
    # action_stage meta
    image = 'thb-card-ppoint'
    name = u'P点'
    description = (
        u'|RP点|r\n\n'
        u'出牌阶段使用，你摸一张牌，并且获得牌面点数数量的P点。\n'
        u'|B|R>> |rP点是商店中使用的货币，可以用来向其他人购买物品、抽奖。\n'
        u'|B|R>> |rP点的获得不会影响当前的游戏进程。'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'获得P点！')


class CollectPPoint:

    def effect_string_before(act):
        return '|G【%s】|r获得了%s点|GP点|r！' % (
            act.target.ui_meta.char_name,
            act.associated_card.number,
        )
