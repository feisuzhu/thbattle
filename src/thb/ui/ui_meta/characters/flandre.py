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
    name        = u'芙兰朵露'
    title       = u'恶魔之妹'
    illustrator = u'月见'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-flandre'
    figure_image      = u'thb-figure-flandre'
    miss_sound_effect = u'thb-cv-flandre_miss'


class CriticalStrike:
    # Skill
    name = u'狂咲'
    description = (
        u'摸牌阶段，你可以少摸一张牌，若如此做，你获得以下效果直到回合结束：\n'
        u'|B|R>> |r当你没有干劲时，你可以对本阶段内没有成为过|G弹幕|r目标的其他角色使用|G弹幕|r。\n'
        u'|B|R>> |r你为伤害来源的|G弹幕|r和|G弹幕战|r造成的伤害+1。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CriticalStrikeHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【狂咲】吗？'


class CriticalStrikeLimit:
    target_independent = False
    shootdown_message = u'你对这个角色使用过弹幕了'


class CriticalStrikeAction:
    def effect_string(act):
        return u'|G【%s】|r突然呵呵一笑，进入了黑化状态！' % (
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-flandre_cs'


class Exterminate:
    # Skill
    name = u'毁灭'
    description = u'|B锁定技|r，每当你使用|G弹幕|r或|G弹幕战|r指定其他角色为目标后，其所有技能无效直到回合结束。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ExterminateAction:
    def effect_string(act):
        return u'|G【%s】|r被|G【%s】|r玩坏了……' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return None
        return 'thb-cv-flandre_cs'
