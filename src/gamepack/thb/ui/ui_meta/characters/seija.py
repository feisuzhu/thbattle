# -*- coding: utf-8 -*-

import random

from gamepack.thb import actions
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.seija)


class InciteAttack:
    name = u'挑拨'

    def effect_string(act):
        return u'|G【%s】|r立刻将|G弹幕|r甩在了|G【%s】|r的脸上：“看也就看了，能别说么？”' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class InciteFailAttack:
    name = u'挑拨'

    def effect_string(act):
        return u'|G【%s】|r立刻将|G弹幕|r甩在了|G【%s】|r的脸上：“你怎么知道是蓝白条的？”' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class InciteSilentFailAction:
    def effect_string(act):
        return u'|G【%s】|r低头看了一眼，诶，好像真的是蓝白条……' % (
            act.target.ui_meta.char_name,
        )


class Incite:
    # Skill
    name = u'挑拨'
    custom_ray = True

    def clickable(game):
        try:
            if limit1_skill_used('incite_tag'):
                return False
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True
        except IndexError:
            pass

        return False

    def is_action_valid(g, cl, tl):
        if cl[0].associated_cards:
            return (False, u'请不要选择牌！')

        if not len(tl):
            return (False, u'请选择第一名玩家（【拼点】的对象）')
        elif len(tl) == 1:
            return (False, u'请选择第二名玩家（【弹幕】的目标）')
        else:
            return (True, u'大嘴正邪愉快的一天开始了～')

    def effect_string(act):
        src = act.source
        tgt, victim = act.target_list
        if victim is src:
            return u'|G【%s】|r一脸坏笑，对|G【%s】|r说：“那个啥…… 蓝白条，赞！”' % (
                src.ui_meta.char_name,
                tgt.ui_meta.char_name,
            )
        else:
            return u'|G【%s】|r一脸坏笑，对|G【%s】|r说：“你知道吗，|G【%s】|r刚才看了你的胖次，蓝白条，赞！”' % (
                src.ui_meta.char_name,
                tgt.ui_meta.char_name,
                victim.ui_meta.char_name,
            )

    def sound_effect(act):
        return random.choice([
            gres.cv.seija_incite1,
            gres.cv.seija_incite2,
        ])


class InciteAction:
    # choose_option
    choose_option_buttons = ((u'使用', True), (u'不使用', False))

    def ray(act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]

    def choose_option_prompt(act):
        return u'你要对【%s】使用【弹幕】吗？' % act.source.ui_meta.char_name


class Reversal:
    # Skill
    name = u'逆转'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ReversalDuel:
    name = u'逆转'

    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r：“你敢打我脸，我就敢打回去！”' % (
            act.target.ui_meta.char_name,
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return gres.cv.seija_reversal


class ReversalHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【逆转】吗？'


class Seija:
    # Character
    char_name = u'鬼人正邪'
    port_image = gres.seija_port
    miss_sound_effect = gres.cv.seija_miss
    description = (
        u'|DB逆袭的天邪鬼 鬼人正邪 体力：3|r\n\n'
        u'|G挑拨|r：出牌阶段，你可以与一名角色拼点，若你赢，视为该角色对其攻击范围内一名由你指定的角色使用了一张【弹幕】。若你没赢，该角色可以视为对你使用了一张【弹幕】。每阶段限一次。\n\n'
        u'|G逆转|r：你受到【弹幕】效果时，你可以摸一张牌，然后若此时你的手牌数大于该角色，此弹幕对你无效并视为该角色对你使用了一张【弹幕战】。\n\n'
        u'|DB（画师：Pixiv ID 37885158，CV：北斗夜）|r'
    )
