# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.medicine.Medicine)
class Medicine:
    # Character
    name        = '梅蒂欣'
    title       = '小小的甜蜜毒药'
    illustrator = '和茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-medicine'
    figure_image      = 'thb-figure-medicine'
    miss_sound_effect = 'thb-cv-medicine_miss'

    notes = 'KOF不平衡角色'


@ui_meta(characters.medicine.Ciguatera)
class Ciguatera:
    # Skill
    name = '神经之毒'
    description = '一名角色准备阶段开始时，你可以弃置一张黑色牌，令其流失1点体力并获得<style=B>喝醉</style>状态。'


@ui_meta(characters.medicine.CiguateraAction)
class CiguateraAction:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}使用了<style=Skill.Name>神经之毒</style>。'

    def sound_effect(self, act):
        return 'thb-cv-medicine_ciguatera'


@ui_meta(characters.medicine.CiguateraHandler)
class CiguateraHandler:
    def choose_card_text(self, act, cards):
        return act.cond(cards), '弃置一张黑色牌，发动<style=Skill.Name>神经之毒</style>'


@ui_meta(characters.medicine.Melancholy)
class Melancholy:
    # Skill
    name = '忧郁之毒'
    description = '每当你受到一次有来源的伤害后，你可以展示并获得牌堆顶的一张牌，若此牌不是梅花牌，伤害来源不能使用或打出手牌，直到回合结束。'


@ui_meta(characters.medicine.MelancholyPoison)
class MelancholyPoison:
    name = '忧郁之毒(效果)'

    def is_complete(self, skill):
        return (False, '<style=Card.Name>忧郁之毒</style>：无法使用或打出手牌直到该回合结束')

    def is_action_valid(self, sk, tl):
        return (False, '<style=Card.Name>忧郁之毒</style>：无法使用或打出手牌直到该回合结束')


@ui_meta(characters.medicine.MelancholyAction)
class MelancholyAction:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}使用了<style=Skill.Name>忧郁之毒</style>。'

    def effect_string(self, act):
        tgt = act.target
        if act.effective:
            return f'{N.char(tgt)}陷入了忧郁。'
        else:
            return f'似乎对{N.char(tgt)}没有效果。'

    def sound_effect(self, act):
        return 'thb-cv-medicine_melancholy'


@ui_meta(characters.medicine.MelancholyHandler)
class MelancholyHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '是否发动<style=Skill.Name>忧郁之毒</style>'


@ui_meta(characters.medicine.MelancholyLimit)
class MelancholyLimit:
    target_independent = True
    shootdown_message = '<style=Skill.Name>忧郁</style>：你不能使用或打出手牌'
