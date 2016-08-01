# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.aya)


class UltimateSpeed:
    # Skill
    name = u'最速'
    description = u'|B锁定技|r，你的回合内，当你使用本回合的第二张牌时，你摸一张牌，然后你使用卡牌时无距离限制，直到回合结束。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class UltimateSpeedAction:
    def effect_string(act):
        return u'|G【%s】|r：“哼哼，你已经跟不上我的速度了吧～”' % (
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-aya_ultimatespeed'


class Aya:
    # Character
    name        = u'射命丸文'
    title       = u'幻想乡最速'
    illustrator = u'渚FUN'
    cv          = u'君寻'

    port_image        = u'thb-portrait-aya'
    figure_image      = u'thb-figure-aya'
    miss_sound_effect = u'thb-cv-aya_miss'
