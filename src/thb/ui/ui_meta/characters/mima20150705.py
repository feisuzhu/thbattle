# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.mima20150705)


class Mima20150705:
    # Character
    name        = u'魅魔'
    title       = u'魔闪的修罗'
    designer    = u'蝶之羽风暂留此'

    port_image        = u'thb-portrait-mima20150705'


class Tianyi:
    # Skill
    name = u'天仪'
    description = (
        u'你的回合内限一次，一张符卡生效前，你可以使其无效，视为你对该符卡指定的所有目标依次使用一张弹幕。\n'
        u'|B|R>> |r以此法使用的弹幕不受“一回合使用一次”的限制。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Eling:
    # Skill
    name = u'恶灵'
    description = u'|B锁定技|r，一名角色于其回合内受到伤害时，你摸两张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class TianyiHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【天仪】吗？'
