# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


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
	'<style=B>锁定技</style>，你使用<style=Card.Name>弹幕</style>或<style=Card.Name>弹幕战M</style>造成的伤害+1。你没有干劲时可以对出牌阶段内没有成为过<style=Card.Name>弹幕</style>目标的其他角色使用<style=Card.Name>弹幕</style>。回合结束时，如果你内造成过伤害，须弃置一张牌。'
    )


@ui_meta(characters.flandre.CriticalStrikeHandler)
class CriticalStrikeHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>狂咲</style>吗？'


@ui_meta(characters.flandre.CriticalStrikeLimit)
class CriticalStrikeLimit:
    target_independent = False
    shootdown_message = '你对这个角色使用过弹幕了'


@ui_meta(characters.flandre.CriticalStrikeAction)
class CriticalStrikeAction:
    def effect_string(self, act):
        return f'{N.char(act.target)}突然呵呵一笑，进入了黑化状态！'

    def sound_effect(self, act):
        return 'thb-cv-flandre_cs'


@ui_meta(characters.flandre.CriticalStrikeDropAction)
class CriticalStrikeDropAction:
    def effect_string(self, act):
        return f'{N.char(act.target)} 狂咲弃牌效果'

    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '<style=Skill.Name>狂咲</style>：弃置这张牌')
        else:
            return (False, '<style=Skill.Name>狂咲</style>：请弃置一张牌')


@ui_meta(characters.flandre.Exterminate)
class Exterminate:
    # Skill
    name = '毁灭'
    description = '<style=B>锁定技</style>，每当你使用<style=Card.Name>弹幕</style>或<style=Card.Name>弹幕战</style>指定其他角色为目标后，其所有技能无效直到回合结束。'


@ui_meta(characters.flandre.ExterminateAction)
class ExterminateAction:
    def effect_string(self, act):
        return f'{N.char(act.target)}被{N.char(act.source)}玩坏了……'

    def sound_effect(self, act):
        return None
        return 'thb-cv-flandre_cs'
