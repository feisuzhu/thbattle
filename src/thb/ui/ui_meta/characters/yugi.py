# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.yugi)


class Yugi:
    # Character
    name        = u'星熊勇仪'
    title       = u'人所谈论的怪力乱神'
    illustrator = u'渚FUN'
    cv          = u'北斗夜'

    port_image        = u'thb-portrait-yugi'
    figure_image      = u'thb-figure-yugi'
    miss_sound_effect = u'thb-cv-yugi_miss'


class YugiKOF:
    # Character
    name        = u'星熊勇仪'
    title       = u'人所谈论的怪力乱神'
    illustrator = u'渚FUN'
    cv          = u'北斗夜'

    port_image        = u'thb-portrait-yugi'
    figure_image      = u'thb-figure-yugi'
    miss_sound_effect = u'thb-cv-yugi_miss'

    notes = u'|RKOF修正角色|r'


class Assault:
    # Skill
    name = u'强袭'
    description = u'|B锁定技|r，你与其他角色计算距离时始终-1。'

    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AssaultAttack:
    name = u'强袭'

    def sound_effect(act):
        return 'thb-cv-yugi_assaultkof'


class AssaultKOFHandler:
    choose_option_prompt = u'你要发动【强袭】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class AssaultKOF:
    # Skill
    name = u'强袭'
    description = u'|B登场技|r，你登场时可以视为使用了一张|G弹幕|r。'

    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FreakingPower:
    # Skill
    name = u'怪力'
    description = u'每当你使用|G弹幕|r指定了其他角色时，你可以进行一次判定，若结果为红，则此|G弹幕|r不能被响应；若结果为黑，则此|G弹幕|r造成伤害后，你弃置其一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FreakingPowerAction:
    fatetell_display_name = u'怪力'

    def effect_string_before(act):
        return u'|G【%s】|r稍微认真了一下，弹幕以惊人的速度冲向|G【%s】|r' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-yugi_fp'


class FreakingPowerHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【怪力】吗？'
