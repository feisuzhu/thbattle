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


class ForbiddenFruits:
    # Skill
    name = u'禁果'
    description = (
        u'|B锁定技|r，每当你使用|G弹幕|r或|G弹幕战|r造成伤害后，你回复伤害值两倍的体力，你摸以此方式回复的超出体力上限数值等量的牌。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


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
        return 'thb-cv-flandre_cs'
