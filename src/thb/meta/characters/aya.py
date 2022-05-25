# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.aya.UltimateSpeed)
class UltimateSpeed:
    # Skill
    name = '最速'
    description = '<style=B>锁定技</style>，你的回合内，当你使用第一张牌后你使用的卡牌无距离限制；当你使用第二张牌后，你摸一张牌。'


@ui_meta(characters.aya.UltimateSpeedUnleashAction)
class UltimateSpeedUnleashAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}：“哼哼，你已经跟不上我的速度了吧～”'

    def sound_effect(self, act):
        return 'thb-cv-aya_ultimatespeed'


@ui_meta(characters.aya.UltimateSpeedDrawAction)
class UltimateSpeedDrawAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}：“哼哼，还可以更快！”'

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
