# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N
from thb.cards.base import VirtualCard


# -- code --
@ui_meta(characters.yugi.Yugi)
class Yugi:
    # Character
    name        = '星熊勇仪'
    title       = '人所谈论的怪力乱神'
    illustrator = '渚FUN'
    cv          = '北斗夜'

    port_image        = 'thb-portrait-yugi'
    figure_image      = 'thb-figure-yugi'
    miss_sound_effect = 'thb-cv-yugi_miss'


@ui_meta(characters.yugi.YugiKOF)
class YugiKOF:
    # Character
    name        = '星熊勇仪'
    title       = '人所谈论的怪力乱神'
    illustrator = '渚FUN'
    cv          = '北斗夜'

    port_image        = 'thb-portrait-yugi'
    figure_image      = 'thb-figure-yugi'
    miss_sound_effect = 'thb-cv-yugi_miss'

    notes = 'KOF修正角色'


@ui_meta(characters.yugi.Assault)
class Assault:
    # Skill
    name = '强袭'
    description = '<style=B>锁定技</style>，你与其他角色计算距离时始终-1。'


@ui_meta(characters.yugi.AssaultAttack)
class AssaultAttack:
    name = '强袭'

    def sound_effect(self, act):
        return 'thb-cv-yugi_assaultkof'


@ui_meta(characters.yugi.AssaultKOFHandler)
class AssaultKOFHandler:
    choose_option_prompt = '你要发动<style=Skill.Name>强袭</style>吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(characters.yugi.AssaultKOF)
class AssaultKOF:
    # Skill
    name = '强袭'
    description = '<style=B>登场技</style>，你登场时可以视为使用了一张<style=Card.Name>弹幕</style>。'


@ui_meta(characters.yugi.FreakingPower)
class FreakingPower:
    # Skill
    name = '怪力'
    description = '每当你使用<style=Card.Name>弹幕</style>指定了其他角色时，你可以进行一次判定，若结果为红，则此<style=Card.Name>弹幕</style>不能被响应；若结果为黑，则此<style=Card.Name>弹幕</style>造成伤害后，你弃置其一张牌。'


@ui_meta(characters.yugi.FreakingPowerAction)
class FreakingPowerAction:
    fatetell_display_name = '怪力'

    def effect_string_before(self, act):
        return f'{N.char(act.source)}稍微认真了一下，弹幕以惊人的速度冲向{N.char(act.target)}'

    def sound_effect(self, act):
        return 'thb-cv-yugi_fp'


@ui_meta(characters.yugi.FreakingPowerHandler)
class FreakingPowerHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>怪力</style>吗？'


@ui_meta(characters.yugi.SplashProof)
class SplashProof:
    # Skill
    name = '止洒'
    description = '出牌阶段限一次，若你使用的<style=Card.Name>弹幕</style>未造成伤害，你可以获得之。'


@ui_meta(characters.yugi.SplashProofRetrieveAction)
class SplashProofRetrieveAction:
    def effect_string_before(self, act: characters.yugi.SplashProofRetrieveAction):
        c = VirtualCard.unwrap([act.card])
        return f'{N.char(act.source)}算准距离，略微倾斜身体，打出去的{N.card(c)}又回到了手中！'

    def sound_effect(self, act):
        return 'thb-cv-yugi_fp'


@ui_meta(characters.yugi.SplashProofHandler)
class SplashProofHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>止洒</style>吗？'