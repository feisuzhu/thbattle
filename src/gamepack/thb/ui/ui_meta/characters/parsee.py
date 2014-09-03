# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.parsee)


class Parsee:
    # Character
    char_name = u'水桥帕露西'
    port_image = gres.parsee_port
    description = (
        u'|DB地壳下的嫉妒心 水桥帕露西 体力：4|r\n\n'
        u'|G嫉妒|r：出牌阶段，你可以将一张黑色牌当做【城管执法】使用，若以此法使一名距离1以内角色的一张方片牌进入弃牌堆，你可以获得之。\n\n'
        u'|DB（画师：Pixiv ID 2872076）|r'
    )


class Envy:
    # Skill
    name = u'嫉妒'

    def clickable(game):
        me = game.me

        if my_turn() and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        assert skill.is_card(characters.parsee.Envy)
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')
        else:
            c = cl[0]
            if c.suit not in (cards.Card.SPADE, cards.Card.CLUB):
                return (False, u'请选择一张黑色的牌！')
            return cards.DemolitionCard.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        s = u'|G【%s】|r发动了嫉妒技能，将|G%s|r当作|G%s|r对|G【%s】|r使用。' % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            card.treat_as.ui_meta.name,
            target.ui_meta.char_name,
        )
        return s


class EnvyHandler:
    choose_option_buttons = ((u'获得', True), (u'不获得', False))

    def choose_option_prompt(act):
        return u'你要获得【%s】吗？' % act.card.ui_meta.name


class EnvyRecycleAction:
    def effect_string(act):
        return u'|G【%s】|r：“喂喂这么好的牌扔掉不觉得可惜么？不要嫉妒我。”' % (
            act.source.ui_meta.char_name
        )
