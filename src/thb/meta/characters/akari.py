# -*- coding: utf-8 -*-


# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import passive_clickable, passive_is_action_valid, ui_meta


# -- code --


@ui_meta(characters.akari.AkariSkill)
class AkariSkill:
    # Skill
    name = '阿卡林'
    description = '消失在画面里的能力。在开局之前没有人知道这是谁。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.akari.Akari)
class Akari:
    # Character
    name        = '随机角色'
    title       = '会是谁呢'

    port_image  = 'thb-portrait-akari'
