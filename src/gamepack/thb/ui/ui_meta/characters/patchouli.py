# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.patchouli)


class Library:
    # Skill
    name = u'图书'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class LibraryDrawCards:
    def effect_string(act):
        return u'|G【%s】|r发动了|G图书|r技能，摸1张牌。' % (
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return random.choice([
            'thb-cv-patchouli_library1',
            'thb-cv-patchouli_library2',
        ])


class Knowledge:
    # Skill
    name = u'博学'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class KnowledgeAction:
    def effect_string(act):
        return u'|G【%s】|r一眼就看穿了这张符卡，直接挡下。' % (
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-patchouli_knowledge'


class Patchouli:
    # Character
    char_name = u'帕秋莉'
    port_image = 'thb-portrait-patchouli'
    figure_image = 'thb-figure-patchouli'
    miss_sound_effect = 'thb-cv-patchouli_miss'
    description = (
        u'|DB不动的大图书馆 帕秋莉 体力：3|r\n\n'
        u'|G图书|r：|B锁定技|r，当你使用一张非延时符卡时，你摸一张牌。\n\n'
        u'|G博学|r：|B锁定技|r，黑桃符卡对你无效。\n\n'
        u'|DB（画师：ideolo@NEKO WORKi，CV：shourei小N）|r'
    )
