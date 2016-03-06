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
    char_name = u'星熊勇仪'
    port_image = 'thb-portrait-yugi'
    figure_image = 'thb-figure-yugi'
    miss_sound_effect = 'thb-cv-yugi_miss'
    description = (
        u'|DB人所谈论的怪力乱神 星熊勇仪 体力：4|r\n\n'
        # u'|G强袭|r：你可以自损1点体力，或者使用一张武器牌/【酒】，对任意一名在你的攻击范围内的玩家造成一点伤害。\n\n'
        u'|G强袭|r：|B锁定技|r，你与其他角色计算距离时始终-1。\n\n'
        u'|G怪力|r：当你使用【弹幕】指定一名其他角色成为目标后，你可以进行一次判定：若结果为红色，则此【弹幕】不可闪避；若结果为黑色，则此【弹幕】造成伤害后你可以弃置其一张牌。\n\n'
        u'|DB（画师：渚FUN，CV：北斗夜）|r'
    )


class YugiKOF:
    # Character
    char_name = u'星熊勇仪'
    port_image = 'thb-portrait-yugi'
    figure_image = 'thb-figure-yugi'
    miss_sound_effect = 'thb-cv-yugi_miss'
    description = (
        u'|DB人所谈论的怪力乱神 星熊勇仪 体力：4|r\n\n'
        u'|G强袭|r：|B登场技|r，你登场时可以视为对对手使用了一张|G弹幕|r。\n\n'
        u'|G怪力|r：当你使用|G弹幕|r指定一名其他角色成为目标后，你可以进行一次判定：若结果为红色，则此|G弹幕|r不可闪避；若结果为黑色，则此|G弹幕|r造成伤害后你可以弃置其一张牌。\n\n'
        u'|RKOF修正角色|r\n\n'
        u'|DB（画师：渚FUN，CV：北斗夜）|r'
    )


class Assault:
    # Skill
    name = u'强袭'
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
    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FreakingPower:
    # Skill
    name = u'怪力'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class FreakingPowerAction:
    fatetell_display_name = u'怪力'

    def effect_string_before(act):
        return u'|G【%s】|r稍微认真了一下，弹幕以惊人的速度冲向|G【%s】|r' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-yugi_fp'


class FreakingPowerHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【怪力】吗？'
