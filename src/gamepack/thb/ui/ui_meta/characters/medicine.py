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
        u'|G神经之毒|r：一名角色的准备阶段开始时，你可以弃置一张黑色牌，令该角色获得|G喝醉|r状态。若该角色在该回合结束阶段开始时处于|G喝醉|r状态，其失去|G喝醉|r状态并选择一项：①弃置一张手牌并令你摸一张牌；②受到一点无来源伤害。\n\n'
        u'|G忧郁之毒|r：每当你受到X点有来源的伤害后，你可以摸X张牌并展示，若其中至少一张不为梅花，伤害来源无法使用或打出手牌直到该回合结束。'
    )


class Ciguatera:
    # Skill
    name = u'神经之毒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CiguateraAction:
    pass


class CiguateraTurnEnd:
    def choose_card_text(g, act, cards):
        return act.cond(cards), u'受到一点无来源伤害，或者弃置一张手牌并让【%s】摸一张牌' % act.source.ui_meta.char_name


class CiguateraHandler:
    def choose_card_text(g, act, cards):
        return act.cond(cards), u'弃置一张黑色牌，发动【神经之毒】'


class Melancholy:
    # Skill
    name = u'忧郁之毒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MelancholyAction:
    pass


class MelancholyHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'是否发动【忧郁之毒】'

