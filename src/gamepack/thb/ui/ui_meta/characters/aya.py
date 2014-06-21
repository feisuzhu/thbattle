# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.aya)


class UltimateSpeed:
    # Skill
    name = u'最速'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class UltimateSpeedHandler:
    choose_option_buttons = ((u'摸一张牌', 'draw'), (u'无距离限制', 'range'), (u'不发动', None))
    choose_option_prompt = u'请选择【最速】的效果'


class Aya:
    # Character
    char_name = u'射命丸文'
    port_image = gres.aya_port
    figure_image = gres.aya_figure
    description = (
        u'|DB幻想乡最速 射命丸文 体力：4|r\n\n'
        u'|G最速|r：在你的回合内，你每使用两张牌便可以选择一项：①摸一张牌；②你在回合内使用的下一张牌无距离限制。\n\n'
        u'|RKOF模式下不可用\n\n'
        u'|DB（画师：渚FUN）|r'
    )
