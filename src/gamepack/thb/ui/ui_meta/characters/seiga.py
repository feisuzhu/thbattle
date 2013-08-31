# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.seiga)


class Seiga:
    # Character
    char_name = u'霍青娥'
    port_image = gres.seiga_port
    description = (
        u'|DB僵尸别跑 霍青娥 体力：4|r\n\n'
        u'|G邪仙|r：你的回合内，你可以将一张可以主动发动的手牌交给任意一名玩家，并以该玩家的身份立即使用。\n'
        u'|B|R>> |r以此方法使用弹幕时，弹幕的“一回合一次”的限制由你来承担\n'
        u'|B|R>> |r在结算的过程中，你可以选择跳过指向多人的卡牌效果结算。'

        # u'|G穿墙|r：当你成为可指向多人的卡牌、技能的目标时，你可以使该效果无效并摸一张牌。'
    )


class HeterodoxyHandler:
    # choose_option meta
    choose_option_buttons = ((u'跳过结算', True), (u'正常结算', False))
    choose_option_prompt = u'你要跳过当前的卡牌结算吗？'


class HeterodoxySkipAction:
    def effect_string(act):
        return u'|G【%s】|r跳过了卡牌效果的结算' % (
            act.source.ui_meta.char_name,
        )


class HeterodoxyAction:
    def ray(act):
        return [(act.source, act.target_list[0])]


class Heterodoxy:
    # Skill
    name = u'邪仙'
    custom_ray = True

    def clickable(g):
        if not my_turn(): return False

        me = g.me
        return bool(me.cards or me.showncards or me.equips)

    def effect_string(act):
        return u'|G【%s】|r发动了邪仙技能，以|G【%s】|r的身份使用了卡牌' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def is_action_valid(g, cl, tl):
        acards = cl[0].associated_cards
        if (not acards) or len(acards) != 1:
            return (False, u'请选择一张手牌')

        card = acards[0]

        if card.resides_in.type not in ('cards', 'showncards'):
            return (False, u'请选择一张手牌!')

        if card.is_card(cards.Skill):
            return (False, u'你不可以像这样组合技能')

        if not getattr(card, 'associated_action', None):
            return (False, u'请的选择可以主动发动的卡牌！')

        if not tl:
            return (False, u'请选择一名玩家作为卡牌发起者')

        victim = tl[0]
        _tl, valid = card.target(g, victim, tl[1:])
        return card.ui_meta.is_action_valid(g, [card], _tl)

        # can't reach here
        # return (True, u'僵尸什么的最萌了！')
        # orig
