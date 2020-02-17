# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_is_action_valid, passive_clickable

# -- code --

__metaclass__ = gen_metafunc(characters.reisen)


class Reisen:
    # Character
    name        = u'铃仙'
    title       = u'永琳的首席药品品尝官'
    illustrator = u'镜_Area@幻想梦斗符'
    cv          = u'小羽'

    port_image        = u'thb-portrait-reisen'
    figure_image      = u'thb-figure-reisen'
    miss_sound_effect = u'thb-cv-reisen_miss'


class ReisenKOF:
    # Character
    name        = u'铃仙'
    title       = u'永琳的首席药品品尝官'
    illustrator = u'镜_Area@幻想梦斗符'
    cv          = u'小羽'

    port_image        = u'thb-portrait-reisen'
    figure_image      = u'thb-figure-reisen'
    miss_sound_effect = u'thb-cv-reisen_miss'

    notes = u'|RKOF修正角色|r'


class Lunatic:
    # Skill
    name = u'狂气'
    description = (
        u'当你使用|G弹幕|r或|G弹幕战|r对其他角色造成伤害后，你可以令其获得技能丧心。\n'
        u'|B|R>> |b丧心|r：|B锁定技|r，出牌阶段，你不能使用|G弹幕|r以外的牌；你使用|G弹幕|r只能指定距离最近的目标；结束阶段开始时，你失去此技能。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Discarder:
    # Skill
    name = u'丧心'
    description = u'|B锁定技|r，出牌阶段，你不能使用|G弹幕|r以外的牌；你使用|G弹幕|r只能指定距离最近的目标；结束阶段开始时，你失去此技能。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MahjongDrug:
    # Skill
    name = u'生药'
    description = u'每当你因使用|G麻薯|r回复体力后，你可以获得|B喝醉|r状态。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MahjongDrugAction:
    def effect_string(act):
        return u'|G【%s】|r：“国士无双之药，认准蓝瓶的！”' % act.target.ui_meta.name

    def sound_effect(act):
        return 'thb-cv-reisen_mahjongdrug'


class MahjongDrugHandler:
    choose_option_prompt = u'你要发动【生药】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class LunaticHandler:
    choose_option_prompt = u'你要发动【狂气】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class LunaticAction:
    def effect_string(act):
        return u'|G【%s】|r看着|G【%s】|r的眼睛，突然觉得自己可以打10个！' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-reisen_lunatic%d' % random.choice([1, 2])


class DiscarderAttackOnly:
    target_independent = True
    shootdown_message = u'【丧心】你不能使用弹幕以外的牌'


class DiscarderDistanceLimit:
    shootdown_message = u'【丧心】你只能对离你最近的角色使用弹幕'
