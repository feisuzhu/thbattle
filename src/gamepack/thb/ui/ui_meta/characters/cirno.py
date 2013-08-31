# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.cirno)


class PerfectFreeze:
    # Skill
    name = u'完美冻结'

    @property
    def image(c):
        return c.associated_cards[0].ui_meta.image

    tag_anim = lambda c: gres.tag_frozenfrog
    description = (
        u'|G【琪露诺】|r的技能产生的|G冻青蛙|r'
    )

    def clickable(game):
        me = game.me
        if not my_turn():
            return False

        if me.cards or me.showncards or me.equips:
            return True

        return False

    def is_action_valid(g, cl, target_list):
        skill = cl[0]
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')

        c = cl[0]
        if c.is_card(cards.Skill):
            return (False, u'你不能像这样组合技能')

        if c.suit in (cards.Card.SPADE, cards.Card.CLUB):
            if set(c.category) & {'basic', 'equipment'}:
                return (True, u'PERFECT FREEZE~')

        return (False, u'请选择一张黑色的基本牌或装备牌！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        source = act.source
        card = act.card
        target = act.target
        return (
            u'|G【%s】|r发动了|G完美冻结|r技能，用|G%s|r' +
            u'把|G【%s】|r装进了大冰块里！'
        ) % (
            source.ui_meta.char_name,
            card.associated_cards[0].ui_meta.name,
            target.ui_meta.char_name,
        )


class Cirno:
    # Character
    char_name = u'琪露诺'
    port_image = gres.cirno_port
    description = (
        u'|DB跟青蛙过不去的笨蛋 琪露诺 体力：4|r\n\n'
        u'|G完美冻结|r：出牌阶段，可以将你的任意一张黑色的基本牌或装备牌当【冻青蛙】使用；你可以对与你距离2以内的角色使用【冻青蛙】。'
    )
