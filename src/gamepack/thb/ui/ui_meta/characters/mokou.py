# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, meta_property
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.mokou1)


class Mokou:
    # Character
    char_name = u'藤原妹红'
    port_image = gres.dummy_port
    description = (
        u'|DB蓬莱的不死鸟 藤原妹红 体力：4|r\n\n'
        u'|G浴火|r：回合结束阶段，你可以自减一点体力，然后摸2张牌。\n\n'
        u'|G重生|r：回合开始阶段，你可以弃置X张红色牌，然后回复一点体力并弃掉你判定区的全部牌（X为你的当前体力值）。'
    )


class Ashes:
    # Skill
    name = u'浴火'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AshesAction:
    def effect_string(act):
        return u'|G【%s】|r发动了|G浴火|r。' % (
            act.target.ui_meta.char_name
        )

class AshesHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【浴火】吗？'


class Reborn:
    # Skill
    name = u'重生'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

class RebornAction:
    def effect_string(act):
        return u'|G【%s】|r使用了|G重生|r。' % (
            act.target.ui_meta.char_name
        )

class RebornHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'回复一残机，并弃置判定区所有牌')
        else:
            return (False, u'请选择%d张红色牌' % act.target.life)

__metaclass__ = gen_metafunc(characters.mokou2)


class Mokou:
    # Character
    char_name = u'藤原妹红'
    port_image = gres.dummy_port
    description = (
        u'|DB蓬莱的不死鸟 藤原妹红 体力：4|r\n\n'
        u'|G浴火|r：回合结束阶段，若你的手牌数低于你的当前体力，你可以失去一点体力，摸两张牌。\n\n'
        u'|G重生|r：回合开始阶段，你可以跳过判定阶段和摸牌阶段，然后恢复一点体力。'
    )


class Ashes:
    # Skill
    name = u'浴火'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AshesAction:
    def effect_string(act):
        return u'|G【%s】|r发动了|G浴火|r。' % (
            act.target.ui_meta.char_name
        )

class AshesHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【浴火】吗？'


class Reborn:
    # Skill
    name = u'重生'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

class RebornAction:
    def effect_string(act):
        return u'|G【%s】|r使用了|G重生|r。' % (
            act.target.ui_meta.char_name
        )

class RebornHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【重生】吗？'
