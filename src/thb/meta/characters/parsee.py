# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Card
from thb.cards.classes import DemolitionCard
from thb.meta.common import my_turn, ui_meta


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
    description = '你可以将一张黑色牌当|G城管执法|r使用；每当距离1的其他角色的方块牌被你使用的|G城管执法|r弃置而置入弃牌堆后，你可以获得之。'

    def clickable(self, g):
        me = g.me

        if my_turn() and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(self, g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.parsee.Envy)
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, '请选择一张牌！')
        else:
            c = cl[0]
            if c.suit not in (Card.SPADE, Card.CLUB):
                return (False, '请选择一张黑色的牌！')
            return DemolitionCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = '|G【%s】|r发动了嫉妒技能，将|G%s|r当作|G%s|r对|G【%s】|r使用。' % (
            source.ui_meta.name,
            card.associated_cards[0].ui_meta.name,
            card.treat_as.ui_meta.name,
            target.ui_meta.name,
        )
        return s

    def sound_effect(self, act):
        return 'thb-cv-parsee_envy'


@ui_meta(characters.parsee.EnvyHandler)
class EnvyHandler:
    choose_option_buttons = (('获得', True), ('不获得', False))

    def choose_option_prompt(self, act):
        return '你要获得【%s】吗？' % act.card.ui_meta.name


@ui_meta(characters.parsee.EnvyRecycleAction)
class EnvyRecycleAction:
    def effect_string(self, act):
        return '|G【%s】|r：“喂喂这么好的牌扔掉不觉得可惜么？不要嫉妒我。”' % (
            act.source.ui_meta.name
        )
