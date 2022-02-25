# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N

# -- code --


@ui_meta(characters.reisen.Reisen)
class Reisen:
    # Character
    name        = '铃仙'
    title       = '永琳的首席药品品尝官'
    illustrator = '镜_Area@幻想梦斗符'
    cv          = '小羽'

    port_image        = 'thb-portrait-reisen'
    figure_image      = 'thb-figure-reisen'
    miss_sound_effect = 'thb-cv-reisen_miss'


@ui_meta(characters.reisen.ReisenKOF)
class ReisenKOF:
    # Character
    name        = '铃仙'
    title       = '永琳的首席药品品尝官'
    illustrator = '镜_Area@幻想梦斗符'
    cv          = '小羽'

    port_image        = 'thb-portrait-reisen'
    figure_image      = 'thb-figure-reisen'
    miss_sound_effect = 'thb-cv-reisen_miss'

    notes = 'KOF修正角色'


@ui_meta(characters.reisen.Lunatic)
class Lunatic:
    # Skill
    name = '狂气'
    description = (
        '当你使用<style=Card.Name>弹幕</style>或<style=Card.Name>弹幕战</style>对其他角色造成伤害后，你可以令其获得技能<style=Skill.Name>丧心</style>。'
        '<style=Desc.Li><style=Skill.Name>丧心</style>：<style=B>锁定技</style>，出牌阶段，你不能使用<style=Card.Name>弹幕</style>以外的牌；你使用<style=Card.Name>弹幕</style>只能指定距离最近的目标；结束阶段开始时，你失去此技能。</style>'
    )


@ui_meta(characters.reisen.Discarder)
class Discarder:
    # Skill
    name = '丧心'
    description = '<style=B>锁定技</style>，出牌阶段，你不能使用<style=Card.Name>弹幕</style>以外的牌；你使用<style=Card.Name>弹幕</style>只能指定距离最近的目标；结束阶段开始时，你失去此技能。'


@ui_meta(characters.reisen.MahjongDrug)
class MahjongDrug:
    # Skill
    name = '生药'
    description = '每当你因使用<style=Card.Name>麻薯</style>回复体力后，你可以获得<style=B>喝醉</style>状态。'


@ui_meta(characters.reisen.MahjongDrugAction)
class MahjongDrugAction:
    def effect_string(self, act):
        return f'{N.char(act.target)}：“国士无双之药，认准蓝瓶的！”'

    def sound_effect(self, act):
        return 'thb-cv-reisen_mahjongdrug'


@ui_meta(characters.reisen.MahjongDrugHandler)
class MahjongDrugHandler:
    choose_option_prompt = '你要发动<style=Skill.Name>生药</style>吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(characters.reisen.LunaticHandler)
class LunaticHandler:
    choose_option_prompt = '你要发动<style=Skill.Name>狂气</style>吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(characters.reisen.LunaticAction)
class LunaticAction:
    def effect_string(self, act):
        return f'{N.char(act.target)}看着{N.char(act.source)}的眼睛，突然觉得自己可以打10个！'

    def sound_effect(self, act):
        return 'thb-cv-reisen_lunatic%d' % random.choice([1, 2])


@ui_meta(characters.reisen.DiscarderAttackOnly)
class DiscarderAttackOnly:
    target_independent = True
    shootdown_message = '<style=Skill.Name>丧心</style>：你不能使用弹幕以外的牌'


@ui_meta(characters.reisen.DiscarderDistanceLimit)
class DiscarderDistanceLimit:
    shootdown_message = '<style=Skill.Name>丧心</style>：你只能对离你最近的角色使用弹幕'
