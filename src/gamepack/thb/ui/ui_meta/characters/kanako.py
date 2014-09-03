# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, card_desc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.kanako)


class Kanako:
    # Character
    char_name = u'八坂神奈子'
    port_image = gres.kanako_port
    description = (
        u'|DB妖怪山上的神明 八坂神奈子 体力：4|r\n\n'
        u'|G御柱：|r摸牌阶段，你可以少摸X张牌（X最大为2）发动。你获得以下技能直到回合结束：\n'
        u'|B|R>> |r你与其他玩家结算距离时始终-X\n'
        u'|B|R>> |r当一名其他角色成为你使用的 非延时符卡的唯一目标 或 弹幕目标 时，该角色需弃置X张牌，否则不能使用或打出手牌直到回合结束。\n\n'
        u'|G信仰|r：|B锁定技|r，若你在出牌阶段内对其他角色造成过伤害，出牌阶段结束时你摸一张牌。\n\n'
        u'|DB（画师：yandre.re/post/show/196410）|r'
    )


class Onbashira:
    # Skill
    name = u'御柱'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid
    no_display = False


class OnbashiraTarget:
    def choose_card_text(g, act, cards):
        prompt = u'御柱：弃置%d张牌（否则不能使用/打出手牌）' % act.amount
        return act.cond(cards), prompt

    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r大喊：“|G御柱|r灰过去了！”' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def effect_string(act):
        if act.cards:
            return u'御柱震飞了|G【%s】|r的%s。' % (
                act.target.ui_meta.char_name,
                u'和'.join([card_desc(c) for c in act.cards]),
            )
        else:
            return u'|G【%s】|r惊呆了。' % act.target.ui_meta.char_name


class OnbashiraHandler:
    # choose_option
    choose_option_buttons = ((u'少摸一张', 1), (u'少摸两张', 2), (u'不发动', 0))
    choose_option_prompt = u'少摸X张牌，发动【御柱】'


class OnbashiraAction:
    def effect_string(act):
        if act.amount:
            return u'|G【%s】|r：“大家看，%s根|G御柱|r！”' % (
                act.target.ui_meta.char_name,
                u'零一两三'[act.amount],
            )


class KanakoFaith:
    name = u'信仰'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class KanakoFaithDrawCards:
    def effect_string(act):
        return u'|G【%s】|r：“嘛，只要御柱仍的勤快，|G信仰|r什么总是有的～”' % (
            act.target.ui_meta.char_name,
        )
