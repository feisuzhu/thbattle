# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N

# -- code --


@ui_meta(characters.kaguya.Kaguya)
class Kaguya:
    # Character
    name        = '蓬莱山辉夜'
    title       = '永远的公主殿下'
    illustrator = '噗呼噗呼@星の妄想乡'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-kaguya'
    figure_image      = 'thb-figure-kaguya'
    miss_sound_effect = 'thb-cv-kaguya_miss'


@ui_meta(characters.kaguya.Dilemma)
class Dilemma:
    # Skill
    name = '难题'
    description = '每当一名角色令你回复1点体力后，你可以令其摸一张牌；每当你受到一次伤害后，你可以令伤害来源选择一项：<style=Desc.Li>交给你一张方块牌，</style><style=Desc.Li>流失1点体力。</style>'


@ui_meta(characters.kaguya.DilemmaDamageAction)
class DilemmaDamageAction:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '交出一张方块牌')
        else:
            return (False, '请选择交出一张方块牌（否则流失一点体力）')

    def effect_string_before(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}发动了<style=Skill.Name>难题</style>。'

    def effect_string(self, act):
        if act.peer_action == 'card':
            return f'{N.char(act.target)}给了{N.char(act.source)}一张牌。'
        # elif act.peer_action == 'life':
        #     <handled by LifeLost>

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-kaguya_dilemma1',
            'thb-cv-kaguya_dilemma2',
        ])


@ui_meta(characters.kaguya.DilemmaHealAction)
class DilemmaHealAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}发动了<style=Skill.Name>难题</style>，{N.char(act.target)}摸了一张牌。'

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-kaguya_dilemma1',
            'thb-cv-kaguya_dilemma2',
        ])


@ui_meta(characters.kaguya.DilemmaHandler)
class DilemmaHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))

    def choose_option_prompt(self, act):
        _type = {
            'positive': '正面效果',
            'negative': '负面效果'
        }.get(act.dilemma_type, 'WTF?!')
        return f'你要发动<style=Skill.Name>难题</style>吗（{_type}）？'


@ui_meta(characters.kaguya.ImperishableNight)
class ImperishableNight:
    # Skill
    name = '永夜'
    description = '你的回合外，每当其他角色使用的红色基本牌置入弃牌堆时，你可以将一张红色基本牌或装备牌当<style=Card.Name>封魔阵</style>对其使用。'
    image = None
    tag = 'sealarray'

    def effect_string(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}使用了<style=Skill.Name>永夜</style>。'

    def sound_effect(self, act):
        return 'thb-cv-kaguya_inight'


@ui_meta(characters.kaguya.ImperishableNightHandler)
class ImperishableNightHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))

    def choose_option_prompt(self, act):
        return f'你要发动<style=Skill.Name>永夜</style>吗（对{N.char(act.target)}）？'

    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '陷入永夜吧！')
        else:
            return (False, '请选择一张红色的基本牌或装备牌')
