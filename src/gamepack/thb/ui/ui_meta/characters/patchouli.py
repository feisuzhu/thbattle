# -*- coding: utf-8 -*-

import random

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

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
            gres.cv.patchouli_library1,
            gres.cv.patchouli_library2,
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
        return gres.cv.patchouli_knowledge


class Patchouli:
    # Character
    char_name = u'帕秋莉'
    port_image = gres.patchouli_port
    figure_image = gres.patchouli_figure
    figure_image_alter = gres.patchouli_figure_alter
    miss_sound_effect = gres.cv.patchouli_miss
    description = (
        u'|DB不动的大图书馆 帕秋莉 体力：3|r\n\n'
        u'|G图书|r：|B锁定技|r，每当你使用了一张非延时符卡时，你摸一张牌。\n\n'
        u'|G博学|r：|B锁定技|r，黑桃色符卡对你无效。\n\n'
        u'|DB（画师：渚FUN，CV：shoulei小N）|r'
    )
