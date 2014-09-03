# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.flandre)


class Flandre:
    # Character
    char_name = u'芙兰朵露'
    port_image = gres.flandre_port
    description = (
        u'|DB恶魔之妹 芙兰朵露 体力：4|r\n\n'
        u'|G狂咲|r：在你的摸牌阶段，如果你选择只摸一张牌，那么在你的出牌阶段你可以出任意张【弹幕】，并且【弹幕】和【弹幕战】的伤害为2点，但是对同一目标只能使用一张【弹幕】。\n\n'
        u'|DB（画师：Pixiv ID 10701033）|r'
    )


class CriticalStrike:
    # Skill
    name = u'狂咲'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CriticalStrikeHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【狂咲】吗？'


class CriticalStrikeAction:
    def effect_string(act):
        return u'|G【%s】|r突然呵呵一笑，进入了黑化状态！' % (
            act.target.ui_meta.char_name,
        )
