# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, card_desc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.kanako)


class Kanako:
    # Character
    char_name = u'八坂神奈子'
    port_image = gres.dummy_port
    description = (
        u'|DB妖怪山上的神明 八坂神奈子 体力：4|r\n\n'
        u'|G神威：|r摸牌阶段，你可以少摸X张牌（X最大为2）发动。你获得以下技能直到回合结束：\n'
        u'你计算与其他角色之间距离时 - X；\n'
        u'当一名其他角色成为你使用的 非延时符卡的唯一目标 或 弹幕目标 时，该角色需弃置X张牌，否则不能使用或打出手牌直到回合结束。\n\n'
        u'信仰：锁定技，若你在出牌阶段内对其他角色造成过伤害，出牌阶段结束时你摸一张牌。'
    )


class Divinity:
    # Skill
    name = u'神威'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DivinityTarget:
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'弃置%d张牌' % act.amount)
        else:
            return (False, u'弃置%d张牌' % act.amount)

    def effect_string(act):
        return u'|G【%s】|r在|G【%s】|r的|G神威|r下%s。' % (
            act.target.ui_meta.char_name,
            act.source.ui_meta.char_name,
            u'弄掉了' + u'，'.join([card_desc(c) for c in act.cards])
            if act.cards else u'动弹不得'
        )


class DivinityHandler:
    # choose_option
    choose_option_buttons = ((u'不发动', 0), (u'1', 1), (u'2', 2))
    choose_option_prompt = u'少摸X张牌，发动【神威】'

    def reason_cannot_fire(evt, act):
        return u'你被【神威】怔住了，不能使用或打出手牌。'


class DivinityAction:
    def effect_string(act):
        if act.amount:
            return u'|G【%s】|r少摸了%d张牌，发动了|G神威|r。' % (
                act.target.ui_meta.char_name,
                act.amount
            )


class KanakoFaith:
    name = u'信仰'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid
