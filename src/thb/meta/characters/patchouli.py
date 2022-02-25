# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.patchouli.Library)
class Library:
    # Skill
    name = '图书'
    description = '<style=B>锁定技</style>，每当你使用非延时符卡时，你摸一张牌；你使用符卡无距离限制。'


@ui_meta(characters.patchouli.LibraryDrawCards)
class LibraryDrawCards:
    def effect_string(self, act):
        return f'{N.char(act.source)}发动了<style=Skill.Name>图书</style>技能，摸1张牌。'

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-patchouli_library1',
            'thb-cv-patchouli_library2',
        ])


@ui_meta(characters.patchouli.Knowledge)
class Knowledge:
    # Skill
    name = '博学'
    description = '<style=B>锁定技</style>，黑桃符卡对你无效。'


@ui_meta(characters.patchouli.KnowledgeAction)
class KnowledgeAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}一眼就看穿了这张符卡，直接挡下。'

    def sound_effect(self, act):
        return 'thb-cv-patchouli_knowledge'


@ui_meta(characters.patchouli.Patchouli)
class Patchouli:
    # Character
    name        = '帕秋莉'
    title       = '不动的大图书馆'
    illustrator = '月见'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-patchouli'
    figure_image      = 'thb-figure-patchouli'
    miss_sound_effect = 'thb-cv-patchouli_miss'
