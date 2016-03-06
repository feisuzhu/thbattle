# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import cards, characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, my_turn, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


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

    def effect_string(act):
        return u'唯快不破！|G【%s】|r弃置了%s，开始加速追击！' % (
            act.source.ui_meta.char_name,
            card_desc(act.card),
        )

    def sound_effect(act):
        return 'thb-cv-sp_aya_windwalk'


class WindWalkLaunch:
    pass


class WindWalkAction:
    idle_prompt = u'疾走：请使用摸到的牌（否则结束出牌并跳过弃牌阶段）'

    def choose_card_text(g, act, cards):
        if not act.cond(cards):
            return False, u'疾走：只能使用摸到的牌（或者结束）'
        else:
            return True, u'不会显示……'


class WindWalkSkipAction:
    def effect_string_before(act):
        return u'|G【%s】|r放弃了追击。' % act.target.ui_meta.char_name

    def sound_effect(act):
        return 'thb-cv-sp_aya_windwalk_stop'


class WindWalkTargetLimit:
    # target_independent = True
    shootdown_message = u'你只能对上一张使用的牌的目标角色（或之一）使用。'


class DominanceHandler:
    choose_option_prompt = u'你要发动【风靡】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class DominanceAction:
    def effect_string_before(act):
        return u'|G【%s】|r成功地了搞了个大新闻！' % (
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-sp_aya_dominance'


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
    miss_sound_effect = 'thb-cv-sp_aya_miss'

    description = (
        u'|DB剑圣是谁有我快吗 SP射命丸文 体力：4|r\n\n'
        u'|G疾走|r：出牌阶段，你可以弃置一张牌，然后摸一张牌，对你上一张使用的牌的目标角色（或之一）使用之并重复此流程，否则结束你的回合。\n'
        u'\n'
        u'|G风靡|r：回合结束时，若你本回合的出牌阶段使用了四种花色的牌，你可执行一个额外的回合。\n'
        u'\n'
        u'|DB（人物设计：吹风姬，画师：躲猫，CV：君寻）|r'
    )
