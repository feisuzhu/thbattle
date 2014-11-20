# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.actions import ttags
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn

# -- code --

__metaclass__ = gen_metafunc(characters.koakuma)


class Koakuma:
    # Character
    char_name = u'小恶魔'
    port_image = 'thb-portrait-koakuma'
    figure_image = 'thb-figure-koakuma'
    miss_sound_effect = 'thb-cv-koakuma_miss'
    description = (
        u'|DB图书管理员 小恶魔 体力：4|r\n\n'
        u'|G寻找|r：出牌阶段限一次，你可以弃置任意数量的牌，然后摸等量的牌。\n\n'
        u'|DB（画师：渚FUN/Takibi，CV：VV）|r'
    )


class Find:
    # Skill
    name = u'寻找'

    def clickable(game):
        me = game.me
        if ttags(me)['find']:
            return False

        if my_turn() and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.koakuma.Find)
        if not len(skill.associated_cards):
            return (False, u'请选择需要换掉的牌！')

        if not [g.me] == target_list:
            return (False, 'BUG!!')

        return (True, u'换掉这些牌')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        s = u'|G【%s】|r发动了寻找技能，换掉了%d张牌。' % (
            source.ui_meta.char_name,
            len(card.associated_cards),
        )
        return s

    def sound_effect(act):
        return 'thb-cv-koakuma_find'
