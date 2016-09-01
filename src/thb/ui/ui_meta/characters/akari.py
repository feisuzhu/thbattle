# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.akari)


class AkariSkill:
    # Skill
    name = u'阿卡林'
    description = u'消失在画面里的能力。在开局之前没有人知道这是谁。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Akari:
    # Character
    name        = u'随机角色'
    title       = u'会是谁呢'

    port_image  = u'thb-portrait-akari'
