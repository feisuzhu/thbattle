# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.sp_aya)


class WindWalk:
    # Skill
    name = u'疾风步'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class WindWalkLaunch:
    idle_prompt = u'疾风步：请使用摸到的牌（否则弃置一张牌）'

    def choose_card_text(g, act, cards):
        if not act.cond(cards):
            return False, u'疾风步：只能使用摸到的牌（或者结束）'
        else:
            return True, u'不会显示……'


class WindWalkHandler:
    choose_option_prompt = u'你要发动【疾风步】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class WindWalkAction:

    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'弃置这张牌')
        else:
            return (False, u'请弃置一张手牌')

    def effect_string_before(act):
        return u'唯快不破！|G【%s】|r在一瞬之后已备好了下一招！' % act.target.ui_meta.char_name


class WindWalkDropCards:

    def effect_string(act):
        return u'|G【%s】|r思考片刻，收回了架势，弃掉了%s。' % (
            act.target.ui_meta.char_name, card_desc(act.cards),
        )


class SpAya:
    # Character
    char_name = u'SP射命丸文'
    port_image = 'thb-portrait-sp_aya'
    figure_image = 'thb-figure-sp_aya'
    description = (
        u'|DB剑圣是谁有我快吗 SP射命丸文 体力：4|r\n\n'
        u'|G疾风步|r：出牌阶段，当你使用的一张|G弹幕|r或非群体非延时符卡生效并结算完毕后，你可以摸一张牌并选择：\n'
        u'|B|R>> |r立即使用此牌\n'
        u'|B|R>> |r弃置一张手牌\n'
        u'\n'
        u'|DB（人物设计：吹风姬，画师：躲猫）|r'
    )
