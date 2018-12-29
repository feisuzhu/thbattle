# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import card_desc, ui_meta, passive_clickable
from thb.meta.common import passive_is_action_valid
from utils.misc import BatchList


# -- code --


@ui_meta(characters.shizuha.AutumnWindEffect)
class AutumnWindEffect:
    def effect_string(self, act):
        return '|G秋风|r带走了|G【%s】|r的%s。' % (
            act.target.ui_meta.name,
            card_desc(act.card),
        )


@ui_meta(characters.shizuha.AutumnWindAction)
class AutumnWindAction:

    def effect_string_before(self, act: characters.shizuha.AutumnWindAction):
        tl = BatchList(act.target_list)
        return '当|G秋风|r吹起，|G【%s】|r连牌都拿不住的时候，才回想起，妈妈说的对，要穿秋裤。' % (
            '】|r、|G【'.join(tl.ui_meta.name),
        )

    def sound_effect(self, act):
        return 'thb-cv-shizuha_autumnwind'


@ui_meta(characters.shizuha.Decay)
class Decay:
    # Skill
    name = '凋零'
    description = '|B锁定技|r。你的回合内，每当其他角色失去最后的手牌时，你摸一张牌；你的回合外，每当你受到一次伤害后，当前回合角色于本回合弃牌阶段需额外弃置一张手牌（该效果不可叠加）。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.shizuha.DecayAction)
class DecayAction:

    def effect_string(self, act):
        return '|G【%s】|r觉得屁股凉了一下……' % act.target.ui_meta.name


@ui_meta(characters.shizuha.DecayEffect)
class DecayEffect:

    def effect_string(self, act):
        return '|G【%s】|r的|G凋零|r效果生效了。' % act.target.ui_meta.name

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

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.shizuha.AutumnWindHandler)
class AutumnWindHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【秋风】吗？'

    def target(self, pl):
        if not pl:
            return (False, '秋风：请选择目标玩家')

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
