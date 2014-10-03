# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.kanako)


class Kanako:
    # Character
    char_name = u'八坂神奈子'
    port_image = gres.kanako_port
    miss_sound_effect = gres.cv.kanako_miss
    description = (
        u'|DB山丘与湖泊的化身 八坂神奈子 体力：4|r\n\n'
        u'|G神威|r：摸牌阶段开始时，你可以摸X张牌，然后弃置等量的牌（X为你的当前体力值，且至多为4）。\n\n'
        u'|G神德|r：每名角色的回合限一次，你因为摸牌阶段以外的原因获得牌时，你可以弃置一张手牌并令一名其他角色摸一张牌。\n\n'
        u'|DB（画师：yandre.re/post/show/196410）|r'
    )


class Divinity:
    # Skill
    name = u'神威'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DivinityHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【神威】吗？'


class DivinityAction:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'神威：弃置这些牌')
        else:
            return (False, u'神威：请弃置%d张牌' % act.amount)


class Virtue:
    # Skill
    name = u'神德'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class VirtueHandler:
    def choose_card_text(g, act, cards):
        prompt = u'神德：弃置1张牌，并选择一名其他角色（否则不发动）'
        return act.cond(cards), prompt

    def target(pl):
        if not pl:
            return (False, u'神德：请选择1名玩家')

        return (True, u'神德：选定的目标摸1张牌')


class VirtueAction:
    def effect_string_before(act):
        return u'kanako 神德'
