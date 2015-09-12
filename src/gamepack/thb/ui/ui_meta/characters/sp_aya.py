# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters, cards
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid, my_turn


# -- code --
__metaclass__ = gen_metafunc(characters.sp_aya)


class WindWalk:
    # Skill
    name = u'疾走'

    def clickable(g):
        if not my_turn():
            return False

        me = g.me
        return bool(me.cards or me.showncards or me.equips)

    def is_action_valid(g, cl, tl):
        acards = cl[0].associated_cards
        if (not acards) or len(acards) != 1:
            return (False, u'请选择一张牌')

        card = acards[0]

        if card.resides_in.type not in ('cards', 'showncards', 'equips'):
            return (False, u'请选择一张牌!')

        if card.is_card(cards.Skill):
            return (False, u'你不可以像这样组合技能')

        return (True, u'疾走')


class WindWalkLaunch:
    pass


class WindWalkAction:
    idle_prompt = u'疾走：请使用摸到的牌（否则结束出牌并跳过弃牌阶段）'

    def choose_card_text(g, act, cards):
        if not act.cond(cards):
            return False, u'疾走：只能使用摸到的牌（或者结束）'
        else:
            return True, u'不会显示……'

    def effect_string_before(act):
        return u'唯快不破！|G【%s】|r在一瞬之后已备好了下一招！' % act.target.ui_meta.char_name


class WindWalkSkipAction:
    def effect_string_before(act):
        return u'|G【%s】|r放弃了追击。' % act.target.ui_meta.char_name


class DominanceHandler:
    choose_option_prompt = u'你要发动【风靡】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class Dominance:
    # Skill
    name = u'风靡'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SpAya:
    # Character
    char_name = u'SP射命丸文'
    port_image = 'thb-portrait-sp_aya'
    figure_image = 'thb-figure-sp_aya'
    description = (
        u'|DB剑圣是谁有我快吗 SP射命丸文 体力：4|r\n\n'
        u'|G疾走|r：出牌阶段，你可弃置一张牌；若你如此做，你亮出牌堆顶的一张牌，并选择：1.立刻使用之，然后重复此流程。2.获得此牌，并结束此回合。\n'
        u'\n'
        u'|G风靡|r：回合结束时，若你本回合的出牌阶段使用了四种花色的牌，你可执行一个额外的回合。\n'
        u'\n'
        u'|DB（人物设计：吹风姬，画师：躲猫）|r'
    )
