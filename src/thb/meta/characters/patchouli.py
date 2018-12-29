# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid

# -- code --


@ui_meta(characters.patchouli.Library)
class Library:
    # Skill
    name = '图书'
    description = '|B锁定技|r，每当你使用非延时符卡时，你摸一张牌；你使用符卡无距离限制。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.patchouli.LibraryDrawCards)
class LibraryDrawCards:
    def effect_string(self, act):
        return '|G【%s】|r发动了|G图书|r技能，摸1张牌。' % (
            act.source.ui_meta.name,
        )

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-patchouli_library1',
            'thb-cv-patchouli_library2',
        ])


@ui_meta(characters.patchouli.Knowledge)
class Knowledge:
    # Skill
    name = '博学'
    description = '|B锁定技|r，黑桃符卡对你无效。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.patchouli.KnowledgeAction)
class KnowledgeAction:
    def effect_string(self, act):
        return '|G【%s】|r一眼就看穿了这张符卡，直接挡下。' % (
            act.source.ui_meta.name,
        )

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
