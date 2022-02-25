# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb.cards import base
from thb.meta.common import ui_meta


# -- code --
@ui_meta(base.CardList)
class CardList:
    lookup = {
        'cards':      '手牌区',
        'showncards': '明牌区',
        'equips':     '装备区',
        'fatetell':   '判定区',
        'faiths':     '信仰',

        # for skills
        'yukari_dimension': '隙间',
        'meirin_qiliao':    '气',
        'momiji-sentry-cards': '哨戒',
    }


@ui_meta(base.HiddenCard)
class HiddenCard:
    image = 'thb-card-hidden'
    name = '隐藏卡片'
    description = '隐藏卡片：这张卡片你看不到'

    def is_action_valid(self, c, tl):
        return (False, '这是BUG，你没法发动这张牌…')


@ui_meta(base.ShreddedCard)
class ShreddedCard:
    image = 'thb-card-hidden'
    name = '被撕碎的卡片'
    description = '被撕碎的卡片：你不应该看到这个，这是个 BUG'

    def is_action_valid(self, c, tl):
        return (False, '这是BUG，你没法发动这张牌…')
