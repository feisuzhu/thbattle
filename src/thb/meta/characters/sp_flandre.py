# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.sp_flandre.SpFlandre)
class SpFlandre:
    # Character
    name        = 'SP芙兰朵露'
    title       = '玩坏你哦'
    illustrator = 'Vivicat@幻想梦斗符'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-sp_flandre'
    figure_image      = 'thb-figure-sp_flandre'
    miss_sound_effect = 'thb-cv-spflandre_miss'


@ui_meta(characters.sp_flandre.DestructionImpulse)
class DestructionImpulse:
    # Skill
    name = '破坏冲动'
    description = '<style=B>锁定技</style>，结束阶段结束后，若你本回合没有造成过伤害，你对距离最近的一名其他角色造成1点伤害，并失去1点体力。'


@ui_meta(characters.sp_flandre.DestructionImpulseAction)
class DestructionImpulseAction:
    def effect_string_before(self, act):
        return f'“来陪我玩好不好呀？”，{N.char(act.source)}对{N.char(act.target)}说道。'

    def sound_effect(self, act):
        return 'thb-cv-spflandre_destructionimpulse'


@ui_meta(characters.sp_flandre.DestructionImpulseHandler)
class DestructionImpulseHandler:
    def choose_card_text(self, act, cards):
        if cards:
            return (False, '请不要选择牌！')

        return (True, '玩坏你哦')

    # choose_players
    def target(self, pl):
        if not pl:
            return (False, '请选择1名距离最近的玩家，对其造成一点伤害')

        return (True, '玩坏你哦')


@ui_meta(characters.sp_flandre.FourOfAKind)
class FourOfAKind:
    # Skill
    name = '四重存在'
    description = '每当你受到一次不大于你当前体力值的伤害时，你可以减少1点体力上限并防止此伤害；你体力值为1时，你为伤害来源的卡牌造成的伤害+1。'


@ui_meta(characters.sp_flandre.FourOfAKindHandler)
class FourOfAKindHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>四重存在</style>吗？'


@ui_meta(characters.sp_flandre.FourOfAKindAction)
class FourOfAKindAction:
    def effect_string(self, act):
        return f'{N.char(act.target)}发动了<style=Skill.Name>四重存在</style>，防止了此次伤害。'

    def sound_effect(self, act):
        return 'thb-cv-spflandre_fourofakind'
