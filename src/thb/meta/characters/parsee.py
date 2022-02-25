# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Card
from thb.cards.classes import DemolitionCard
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.parsee.Parsee)
class Parsee:
    # Character
    name        = '水桥帕露西'
    title       = '地壳下的嫉妒心'
    illustrator = '和茶'
    cv          = '小羽'

    port_image        = 'thb-portrait-parsee'
    figure_image      = 'thb-figure-parsee'
    miss_sound_effect = 'thb-cv-parsee_miss'


@ui_meta(characters.parsee.Envy)
class Envy:
    # Skill
    name = '嫉妒'
    description = '你可以将一张黑色牌当<style=Card.Name>城管执法</style>使用；每当距离1的其他角色的方块牌被你使用的<style=Card.Name>城管执法</style>弃置而置入弃牌堆后，你可以获得之。'

    def clickable(self):
        me = self.me

        if self.my_turn() and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(self, sk, tl):
        skill = sk
        assert skill.is_card(characters.parsee.Envy)
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, '请选择一张牌！')
        else:
            c = sk
            if c.suit not in (Card.SPADE, Card.CLUB):
                return (False, '请选择一张黑色的牌！')
            return DemolitionCard().ui_meta.is_action_valid([skill], tl)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        src, tgt = act.source, act.target
        sk = act.card
        c = sk.associated_cards[0]
        return f'{N.char(src)}发动了嫉妒技能，将{N.card(c)}当作{N.char(sk.treat_as)}对{N.char(tgt)}使用。'

    def sound_effect(self, act):
        return 'thb-cv-parsee_envy'


@ui_meta(characters.parsee.EnvyHandler)
class EnvyHandler:
    choose_option_buttons = (('获得', True), ('不获得', False))

    def choose_option_prompt(self, act):
        return f'你要获得{N.card(act.card)}吗？'


@ui_meta(characters.parsee.EnvyRecycleAction)
class EnvyRecycleAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}：“喂喂这么好的牌扔掉不觉得可惜么？不要嫉妒我。”'
