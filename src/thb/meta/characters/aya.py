# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid

# -- code --


@ui_meta(characters.aya.UltimateSpeed)
class UltimateSpeed:
    # Skill
    name = '最速'
    description = '|B锁定技|r，你的回合内，当你使用本回合的第二张牌时，你摸一张牌，然后你使用卡牌时无距离限制，直到回合结束。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.aya.UltimateSpeedAction)
class UltimateSpeedAction:
    def effect_string(self, act):
        return '|G【%s】|r：“哼哼，你已经跟不上我的速度了吧～”' % (
            act.source.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-aya_ultimatespeed'


@ui_meta(characters.aya.Aya)
class Aya:
    # Character
    name        = '射命丸文'
    title       = '幻想乡最速'
    illustrator = '渚FUN'
    cv          = '君寻'

    port_image        = 'thb-portrait-aya'
    figure_image      = 'thb-figure-aya'
    miss_sound_effect = 'thb-cv-aya_miss'
