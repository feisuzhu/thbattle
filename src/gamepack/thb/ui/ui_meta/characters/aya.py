# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.aya)


class UltimateSpeed:
    # Skill
    name = u'最速'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class UltimateSpeedAction:
    def effect_string(act):
        return u'|G【%s】|r：“哼哼，你已经跟不上我的速度了吧～”' % (
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-aya_ultimatespeed'


class Aya:
    # Character
    char_name = u'射命丸文'
    port_image = 'thb-portrait-aya'
    figure_image = 'thb-figure-aya'
    miss_sound_effect = 'thb-cv-aya_miss'
    description = (
        u'|DB幻想乡最速 射命丸文 体力：4|r\n\n'
        u'|G最速|r：|B锁定技|r，你在回合内使用第二张牌时，你摸一张牌且在本回合使用卡牌时无距离限制。\n\n'
        u'|DB（画师：渚FUN，CV：君寻）|r'
    )
