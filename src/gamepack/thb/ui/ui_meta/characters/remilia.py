# -*- coding: utf-8 -*-

import random

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.remilia)


class SpearTheGungnir:
    # Skill
    name = u'神枪'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SpearTheGungnirAction:
    def effect_string(act):
        return u'|G【%s】|r举起右手，将|G弹幕|r汇聚成一把命运之矛，向|G【%s】|r掷去！' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return random.choice([
            gres.cv.remilia_spearthegungnir1,
            gres.cv.remilia_spearthegungnir2,
        ])


class SpearTheGungnirHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【神枪】吗？'


class VampireKiss:
    # Skill
    name = u'红魔之吻'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class VampireKissAction:
    def effect_string_before(act):
        return u'|G【%s】|r:“B型血，赞！”' % (
            act.source.ui_meta.char_name
        )

    def sound_effect(act):
        return gres.cv.remilia_vampirekiss


class Remilia:
    # Character
    char_name = u'蕾米莉亚'
    port_image = gres.remilia_port
    miss_sound_effect = gres.cv.remilia_miss
    description = (
        u'|DB永远幼小的红月 蕾米莉亚 体力：4|r\n\n'
        u'|G神枪|r：出牌阶段，出现以下情况之一，你可以令你的【弹幕】不能被【擦弹】抵消：\n'
        u'|B|R>> |r目标角色的体力值 大于 你的体力值。\n'
        u'|B|R>> |r目标角色的手牌数 小于 你的手牌数。\n\n'
        u'|G红魔之吻|r：|B锁定技|r，对玩家使用红色【弹幕】命中时，回复1点体力值。\n\n'
        u'|DB（画师：Pixiv ID 23780313，CV：VV）|r'
    )
