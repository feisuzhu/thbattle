# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import cards
from gamepack.thb.ui.ui_meta.common import gen_metafunc

# -- code --
__metaclass__ = gen_metafunc(cards)


class CardList:
    lookup = {
        'cards':      u'手牌区',
        'showncards': u'明牌区',
        'equips':     u'装备区',
        'fatetell':   u'判定区',
        'faiths':     u'信仰',

        # for skills
        'yukari_dimension': u'隙间',
        'meirin_qiliao': u'气',
    }


class HiddenCard:
    # action_stage meta
    image = 'thb-card-hidden'
    name = u'隐藏卡片'
    description = u'|R隐藏卡片|r\n\n这张卡片你看不到'

    def is_action_valid(g, cl, target_list):
        return (False, u'这是BUG，你没法发动这张牌…')
