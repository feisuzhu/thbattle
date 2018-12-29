# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid

# -- code --


@ui_meta(characters.flandre.Flandre)
class Flandre:
    # Character
    name        = '芙兰朵露'
    title       = '恶魔之妹'
    illustrator = '月见'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-flandre'
    figure_image      = 'thb-figure-flandre'
    miss_sound_effect = 'thb-cv-flandre_miss'


@ui_meta(characters.flandre.CriticalStrike)
class CriticalStrike:
    # Skill
    name = '狂咲'
    description = (
        '摸牌阶段，你可以少摸一张牌，若如此做，你获得以下效果直到回合结束：\n'
        '|B|R>> |r当你没有干劲时，你可以对本阶段内没有成为过|G弹幕|r目标的其他角色使用|G弹幕|r\n'
        '|B|R>> |r你为伤害来源的|G弹幕|r和|G弹幕战|r造成的伤害+1'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.flandre.CriticalStrikeHandler)
class CriticalStrikeHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【狂咲】吗？'


@ui_meta(characters.flandre.CriticalStrikeLimit)
class CriticalStrikeLimit:
    target_independent = False
    shootdown_message = '你对这个角色使用过弹幕了'


@ui_meta(characters.flandre.CriticalStrikeAction)
class CriticalStrikeAction:
    def effect_string(self, act):
        return '|G【%s】|r突然呵呵一笑，进入了黑化状态！' % (
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-flandre_cs'


@ui_meta(characters.flandre.Exterminate)
class Exterminate:
    # Skill
    name = '毁灭'
    description = '|B锁定技|r，每当你使用|G弹幕|r或|G弹幕战|r指定其他角色为目标后，其所有技能无效直到回合结束。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.flandre.ExterminateAction)
class ExterminateAction:
    def effect_string(self, act):
        return '|G【%s】|r被|G【%s】|r玩坏了……' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(self, act):
        return None
        return 'thb-cv-flandre_cs'
