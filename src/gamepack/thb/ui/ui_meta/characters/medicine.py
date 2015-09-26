# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.medicine)


class Medicine:
    # Character
    char_name = u'梅蒂欣'
    port_image = 'thb-portrait-medicine'
    figure_image = 'thb-figure-medicine'
    miss_sound_effect = 'thb-cv-medicine_miss'
    description = (
        u'|DB小小的甜蜜毒药 梅蒂欣 体力：3|r\n\n'
        u'|G神经之毒|r：一名角色的准备阶段开始时，你可以弃置一张手牌，令该角色失去一点残机，然后获得喝醉状态。\n\n'
        u'|G忧郁之毒|r：每当你受到一次有来源的伤害后，你可以展示并获得排堆顶一张牌，若其花色不为梅花，伤害来源无法使用或打出手牌直到该回合结束。\n\n'
        u'|DB（画师：和茶，CV：VV）|r'
    )


class Ciguatera:
    # Skill
    name = u'神经之毒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CiguateraAction:
    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r使用了|G神经之毒|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )

    def sound_effect(act):
        return 'thb-cv-medicine_ciguatera'


class CiguateraHandler:
    def choose_card_text(g, act, cards):
        return act.cond(cards), u'弃置一张手牌，发动【神经之毒】'


class Melancholy:
    # Skill
    name = u'忧郁之毒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MelancholyPoison:
    name = u'忧郁之毒(效果)'

    def is_complete(g, cl):
        return (False, u'忧郁之毒：无法使用或打出手牌直到该回合结束')

    def is_action_valid(g, cl, target_list):
        return (False, u'忧郁之毒：无法使用或打出手牌直到该回合结束')


class MelancholyAction:
    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r使用了|G忧郁之毒|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )

    def effect_string(act):
        return (u'|G【%s】|r陷入了忧郁。' if act.effective
                else u'但|G【%s】|r缓了过来。') % act.target.ui_meta.char_name

    def sound_effect(act):
        return 'thb-cv-medicine_melancholy'


class MelancholyHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'是否发动【忧郁之毒】'


class MelancholyLimit:
    target_independent = True
    shootdown_message = u'【忧郁】你不能使用或打出手牌'
