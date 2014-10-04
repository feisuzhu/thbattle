# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, card_desc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.medicine)


class Medicine:
    # Character
    char_name = u'梅蒂欣'
    port_image = gres.medicine_port
    description = (
        u'|DB 小小的甜蜜毒药 梅蒂欣 体力：3|r\n\n'
        u'|G神经之毒|r：一名角色的准备阶段开始时，你可以弃置一张手牌，令该角色获得喝醉状态。若该角色在该回合结束阶段开始时仍处于喝醉状态，其失去喝醉状态并选择一项：弃置一张手牌并令你摸一张牌或受到一点无来源伤害。\n\n'
        u'|G忧郁之毒|r：每当你受到X点有来源的伤害后，你可以摸X张牌并展示之，若其中有不为梅花的牌，伤害来源无法使用或打出手牌直到该回合结束。\n\n'
        u'|DB（画师：Pixiv ID 38268080）|r'
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


class CiguateraTurnEnd:
    def choose_card_text(g, act, cards):
        return act.cond(cards), u'受到一点无来源伤害，或者弃置一张手牌并让【%s】摸一张牌' % act.target.ui_meta.char_name

    def effect_string_before(act):
        return u'|G【%s】|r受到|G【%s】|r的|G神经之毒|r爆发了。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )

    def effect_string(act):
        if act.card:
            return u'|G【%s】|r弃掉了%s。' % (
                act.source.ui_meta.char_name,
                card_desc(act.card)
            )


class CiguateraHandler:
    def choose_card_text(g, act, cards):
        return act.cond(cards), u'弃置一张手牌，发动【神经之毒】'


class Melancholy:
    # Skill
    name = u'忧郁之毒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MelancholyAction:
    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r使用了|G忧郁之毒|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )

    def effect_string(act):
        return (u'|G【%s】|r陷入了忧郁。' if act.effective
                else u'但|G【%s】|r缓了过来。') % act.target.ui_meta.char_name


class MelancholyHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'是否发动【忧郁之毒】'
