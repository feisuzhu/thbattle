# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.flandre)


class Flandre:
    # Character
    char_name = u'芙兰朵露'
    port_image = 'thb-portrait-flandre'
    figure_image = 'thb-figure-flandre'
    miss_sound_effect = 'thb-cv-flandre_miss'
    description = (
        u'|DB恶魔之妹 芙兰朵露 体力：4|r\n\n'
        u'|G狂咲|r：摸牌阶段，你可以少摸一张牌，若如此做，你获得以下技能直到回合结束：你可以对任意其他角色各使用一张【弹幕】，且使用的【弹幕】和【弹幕战】（你为伤害来源时）造成的伤害+1。 \n\n'
        u'|G毁灭|r：|B锁定技|r，你使用的【弹幕】或【弹幕战】指定一名其他角色成为目标后，该角色无法使用技能直到当前回合结束。\n\n'
        u'|DB（画师：月见，CV：shourei小N）|r'
    )


class CriticalStrike:
    # Skill
    name = u'狂咲'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CriticalStrikeHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【狂咲】吗？'


class CriticalStrikeLimit:
    # overrides AttackLimitExceeded
    target_independent = False


class CriticalStrikeAction:
    def effect_string(act):
        return u'|G【%s】|r突然呵呵一笑，进入了黑化状态！' % (
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-flandre_cs'


class Exterminate:
    # Skill
    name = u'毁灭'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ExterminateAction:
    def effect_string(act):
        return u'|G【%s】|r被|G【%s】|r玩坏了……' % (
            act.target.ui_meta.char_name,
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return None
        return 'thb-cv-flandre_cs'
