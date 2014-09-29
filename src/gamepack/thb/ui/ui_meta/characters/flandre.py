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
    miss_sound_effect = gres.cv.flandre_miss
    description = (
        u'|DB恶魔之妹 芙兰朵露 体力：4|r\n\n'
        u'|G狂咲|r：摸牌阶段，你可以少摸一张牌，若如此做，你获得以下技能直到回合结束：你可以对任意其他角色各使用一张【弹幕】，且使用的【弹幕】和【弹幕战】（你为伤害来源时）造成的伤害+1。 \n\n'
        u'|DB（画师：Pixiv ID 21884840，CV：shourei小N）|r'
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

    def sound_effect(act):
        return gres.cv.flandre_cs
