# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.ui.ui_meta.common import gen_metafunc, my_turn

# -- code --

__metaclass__ = gen_metafunc(characters.koakuma)


class Koakuma:
    # Character
    name        = u'小恶魔'
    title       = u'图书管理员'
    illustrator = u'渚FUN/Takibi'
    cv          = u'VV'

    port_image        = u'thb-portrait-koakuma'
    figure_image      = u'thb-figure-koakuma'
    miss_sound_effect = u'thb-cv-koakuma_miss'


class Find:
    # Skill
    name = u'寻找'
    description = u'出牌阶段限一次，你可以弃置至多X张牌，然后摸等量的牌。（X为场上存活角色数）'

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
        n = len([i for i in g.players if not i.dead])

        if not 0 < len(skill.associated_cards) <= n:
            return (False, u'请选择需要换掉的牌（至多%s张）！' % n)

        if not [g.me] == target_list:
            return (False, 'BUG!!')

        return (True, u'换掉这些牌')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        s = u'|G【%s】|r发动了寻找技能，换掉了%d张牌。' % (
            source.ui_meta.name,
            len(card.associated_cards),
        )
        return s

    def sound_effect(act):
        return 'thb-cv-koakuma_find'
