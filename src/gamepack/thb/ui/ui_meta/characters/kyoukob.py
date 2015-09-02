# -*- coding: utf-8 -*-

# -- stdlib --
import random
import time

# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.kyoukob)


class KyoukoB:
    # Character
    char_name = u'幽谷响子B'
    port_image = 'thb-portrait-akari'
    description = (
        u'|DB幽谷响子B 体力：4|r\n\n'
        u'|G空谷回响|r：出牌阶段限一次，当你使用的弹幕对一名角色造成伤害后，你可以令其获得其范围内由你指定的角色B的某张牌，之后，角色B可以弃置场上一张牌。\n\n'
        u'|G回振|r：当你使用的弹幕对与你距离为X的效果被抵消后，你可以视为对一名与你距离为X-1的角色使用一张弹幕。\n\n'
        u'|DB（人物设计：我勒个去）|r'
    )


class Echo:
    # Skill
    name = u'空谷回响'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Resonance:
    # Skill
    name = u'回振'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class EchoAction:
    # choose_players
    def target(pl):
        if not pl:
            return (False, u'空谷回响：弃置场上一张牌')

        return (True, u'空谷回响···')


class EchoHandler:
    # choose_players
    def target(pl):
        if not pl:
            return (False, u'空谷回响：请选择角色B')

        return (True, u'空谷回响···')


class ResonanceHandler:
    # choose_players
    def target(pl):
        if not pl:
            return (False, u'回振：选择弹幕的目标角色')

        return (True, u'回振！')
