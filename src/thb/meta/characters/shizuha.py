# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N
from utils.misc import BatchList


# -- code --


@ui_meta(characters.shizuha.AutumnWindEffect)
class AutumnWindEffect:
    def effect_string(self, act):
        return f'<style=Skill.Name>秋风</style>带走了{N.char(act.target)}的{N.card(act.card)}。'


@ui_meta(characters.shizuha.AutumnWindAction)
class AutumnWindAction:

    def effect_string_before(self, act: characters.shizuha.AutumnWindAction):
        return f'当<style=Skill.Name>秋风</style>吹起，{N.char(act.target_list)}连牌都拿不住的时候，才回想起，妈妈说的对，要穿秋裤。'

    def sound_effect(self, act):
        return 'thb-cv-shizuha_autumnwind'


@ui_meta(characters.shizuha.Decay)
class Decay:
    # Skill
    name = '凋零'
    description = '<style=B>锁定技</style>。你的回合内，每当其他角色失去最后的手牌时，你摸一张牌；你的回合外，每当你受到一次伤害后，当前回合角色于本回合弃牌阶段需额外弃置一张手牌（该效果不可叠加）。'


@ui_meta(characters.shizuha.DecayAction)
class DecayAction:

    def effect_string(self, act):
        return f'{N.char(act.target)}觉得屁股凉了一下……'


@ui_meta(characters.shizuha.DecayEffect)
class DecayEffect:

    def effect_string(self, act):
        return f'{N.char(act.target)}的<style=Skill.Name>凋零</style>效果生效了。'

    def sound_effect(self, act):
        return 'thb-cv-shizuha_decay'


@ui_meta(characters.shizuha.DecayDrawCards)
class DecayDrawCards:

    def sound_effect(self, act):
        return 'thb-cv-shizuha_decay'


@ui_meta(characters.shizuha.AutumnWind)
class AutumnWind:
    # Skill
    name = '秋风'
    description = '弃牌阶段结束时，你可以弃置至多X名角色各一张牌。（X为你本阶段弃置的手牌数）'


@ui_meta(characters.shizuha.AutumnWindHandler)
class AutumnWindHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>秋风</style>吗？'

    def target(self, pl):
        if not pl:
            return (False, '<style=Skill.Name>秋风</style>：请选择目标玩家')

        return (True, '秋风弃牌')


@ui_meta(characters.shizuha.Shizuha)
class Shizuha:
    # Character
    name        = '秋静叶'
    title       = '寂寞与终焉的象征'
    illustrator = '和茶'
    cv          = 'VV'
    designer    = 'SmiteOfKing'

    port_image        = 'thb-portrait-shizuha'
    figure_image      = 'thb-figure-shizuha'
    miss_sound_effect = 'thb-cv-shizuha_miss'
