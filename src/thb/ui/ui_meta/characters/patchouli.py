# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.patchouli)


class Library:
    # Skill
    name = u'图书'
    description = u'|B锁定技|r，你使用符卡时无距离限制，你使用非延时符卡时摸一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class LibraryDrawCards:
    def effect_string(act):
        return u'|G【%s】|r发动了|G图书|r技能，摸1张牌。' % (
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return random.choice([
            'thb-cv-patchouli_library1',
            'thb-cv-patchouli_library2',
        ])


class Knowledge:
    # Skill
    name = u'博学'
    description = u'|B锁定技|r，黑桃符卡对你无效。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class KnowledgeAction:
    def effect_string(act):
        return u'|G【%s】|r一眼就看穿了这张符卡，直接挡下。' % (
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-patchouli_knowledge'


class Patchouli:
    # Character
    name        = u'帕秋莉'
    title       = u'不动的大图书馆'
    illustrator = u'月见'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-patchouli'
    figure_image      = u'thb-figure-patchouli'
    miss_sound_effect = u'thb-cv-patchouli_miss'
