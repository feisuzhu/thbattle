# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb.ui.ui_meta.common import gen_metafunc

from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(cards)


class CardList:
    lookup = {
        'cards': u'手牌区',
        'showncards': u'明牌区',
        'equips': u'装备区',
        'fatetell': u'判定区',
        'faiths': u'信仰',
    }


class HiddenCard:
    # action_stage meta
    image = gres.card_hidden
    name = u'隐藏卡片'
    description = u'|R隐藏卡片|r\n\n这张卡片你看不到'

    def is_action_valid(g, cl, target_list):
        return (False, u'这是BUG，你没法发动这张牌…')
