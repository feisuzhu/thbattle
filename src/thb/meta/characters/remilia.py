# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.remilia.SpearTheGungnir)
class SpearTheGungnir:
    # Skill
    name = '神枪'
    description = (
        '满足下列条件之一时，你可以令你的<style=Card.Name>弹幕</style>不能被响应：'
        '<style=Desc.Li>目标角色的体力值 大于 你的体力值。</style>'
        '<style=Desc.Li>目标角色的手牌数 小于 你的手牌数。</style>'
    )


@ui_meta(characters.remilia.SpearTheGungnirAction)
class SpearTheGungnirAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}举起右手，将<style=Card.Name>弹幕</style>汇聚成一把命运之矛，向{N.char(act.target)}掷去！'

    def sound_effect(self, act):
        return 'thb-cv-remilia_stg'


@ui_meta(characters.remilia.SpearTheGungnirHandler)
class SpearTheGungnirHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>神枪</style>吗？'


@ui_meta(characters.remilia.VampireKiss)
class VampireKiss:
    # Skill
    name = '红魔之吻'
    description = '<style=B>锁定技</style>，你使用红色<style=Card.Name>弹幕</style>时无距离限制。当你使用红色<style=Card.Name>弹幕</style>对一名其他角色造成伤害后，你回复1点体力。'


@ui_meta(characters.remilia.VampireKissAction)
class VampireKissAction:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}:“B型血，赞！”'

    def sound_effect(self, act):
        return 'thb-cv-remilia_vampirekiss'


@ui_meta(characters.remilia.ScarletMistAttackLimit)
class ScarletMistAttackLimit:
    target_independent = False
    shootdown_message = '红雾：你只能对距离1的角色使用弹幕'


@ui_meta(characters.remilia.ScarletMistAction)
class ScarletMistAction:
    def effect_string(self, act):
        src = act.source
        tl = list(act.target_list)
        try:
            tl.remove(src)
        except Exception:
            pass

        return f'{N.char(src)}释放出了<style=Card.Name>红雾</style>，威严爆表！{N.char(tl)}流了鼻血！'

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-remilia_scarletmist1',
            'thb-cv-remilia_scarletmist2',
        ])


@ui_meta(characters.remilia.ScarletMistEndAction)
class ScarletMistEndAction:
    def effect_string(self, act):
        return '<style=Card.Name>红雾</style>结束了。'


@ui_meta(characters.remilia.ScarletMist)
class ScarletMist:
    name = '红雾'
    description = (
        '<style=B>BOSS技</style>，<style=B>限定技</style>，出牌阶段，你可以选择至多X名其他角色（X为存活道中数量），直到你的下个回合开始阶段，所有角色受到以下影响：'
        '<style=Desc.Li>你与被选择的角色使用<style=Card.Name>弹幕</style>时无视距离，且使用<style=Card.Name>弹幕</style>造成伤害后回复等量的体力。</style>'
        '<style=Desc.Li>其他角色使用<style=Card.Name>弹幕</style>时只能指定距离为1的目标。</style>'
    )

    def clickable(self):
        me = self.me
        return self.my_turn() and not me.tags['scarlet_mist_used']

    def is_action_valid(self, sk, tl):
        if sk.associated_cards:
            return (False, '红雾：请不要选择牌！')

        if not tl:
            return (False, '红雾：选择目标')

        return (True, '红雾：选择这些角色获得增益效果')

    def is_available(self, ch):
        pass


@ui_meta(characters.remilia.Remilia)
class Remilia:
    # Character
    name        = '蕾米莉亚'
    title       = '永远幼小的红月'
    illustrator = '小D@星の妄想乡'
    cv          = 'VV'

    port_image        = 'thb-portrait-remilia'
    figure_image      = 'thb-figure-remilia'
    miss_sound_effect = 'thb-cv-remilia_miss'
