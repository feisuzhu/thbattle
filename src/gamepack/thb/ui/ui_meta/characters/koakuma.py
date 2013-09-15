# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.koakuma)


class Koakuma:
    # Character
    char_name = u'小恶魔'
    port_image = gres.koakuma_port
    figure_image = gres.koakuma_figure
    description = (
        u'|DB图书管理员 小恶魔 体力：4|r\n\n'
        u'|G寻找|r：出牌阶段，你可以弃掉任意数量的牌，然后摸取等量的牌。每回合里，你最多可以使用一次寻找。'
    )


class Find:
    # Skill
    name = u'寻找'

    def clickable(game):
        me = game.me
        if limit1_skill_used('find_tag'):
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
