# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.tenshi)


class Masochist:
    # Skill
    name = u'抖Ｍ'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MasochistHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【抖Ｍ】吗？'


class MasochistAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'给你牌~')
        else:
            return (False, u'请选择你要给出的牌（否则给自己）')

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'给你牌~')

    def effect_string_before(act):
        return u'不过|G【%s】|r好像很享受的样子…' % (
            act.target.ui_meta.char_name,
        )


class Hermit:
    # Skill
    name = u'天人'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Tenshi:
    # Character
    char_name = u'比那名居天子'
    port_image = gres.tenshi_port
    description = (
        u'|DB有顶天的大M子 比那名居天子 体力：3|r\n\n'
        u'|G抖Ｍ|r：每当你受到X点伤害，你可以摸X*2张牌，然后将这些牌分配给任意的角色。\n\n'
        u'|G天人|r：在你的判定结束后，你获得该判定牌。'
    )
