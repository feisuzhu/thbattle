# -*- coding: utf-8 -*-

# -- stdlib --
import random
import time

# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.kyouko)


class Kyouko:
    # Character
    char_name = u'幽谷响子A'
    port_image = 'thb-portrait-akari'
    description = (
        u'|DB幽谷响子A 体力：3|r\n\n'
        u'|G回响|r：当一张牌对你造成伤害后，你可以获得这张牌；如果这张牌是弹幕，你可改令另一名获得这张牌。\n\n'
        u'|G共振|r：当你使用的弹幕对一名角色结算完毕后，你可以选择一名其他角色，其可以立即对该角色使用一张弹幕（无视距离限制）；若其使用的弹幕花色与你所使用的相同，（在结算前）其摸一张牌。'
    )


class Echo:
    # Skill
    name = u'回响'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Resonance:
    # Skill
    name = u'共振'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class EchoHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'放弃', False))
    choose_option_prompt = u'是否发动【回响】'

    # choose_players
    def target(pl):
        if not pl:
            return (False, u'回响：请选择获得【弹幕】的角色')

        return (True, u'回响···')


class ResonanceAction:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'回响：对%s使用弹幕' % act.target.ui_meta.char_name)
        else:
            return (False, u'回响：请选择一张弹幕对%s使用' % act.target.ui_meta.char_name)


class ResonanceHandler:
    # choose_players
    def target(pl):
        if not pl:
            return (False, u'共振：请选择一名角色使用【弹幕】')

        return (True, u'发动【共振】')
