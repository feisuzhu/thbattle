# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, my_turn, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.seija)


class InciteAttack:
    name = u'挑拨'

    def effect_string(act):
        return u'|G【%s】|r立刻将|G弹幕|r甩在了|G【%s】|r的脸上：“看也就看了，能别说么？”' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class InciteFailAttack:
    name = u'挑拨'

    def effect_string(act):
        return u'|G【%s】|r立刻将|G弹幕|r甩在了|G【%s】|r的脸上：“你怎么知道是蓝白条的？”' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class InciteSilentFailAction:
    def effect_string(act):
        return u'|G【%s】|r低头看了一眼，诶，好像真的是蓝白条……' % (
            act.target.ui_meta.name,
        )


class Incite:
    # Skill
    name = u'挑拨'
    description = u'出牌阶段限一次，你可以与一名其他角色拼点，若你赢，视为该角色对其攻击范围内你指定的另一名其他角色使用了一张|G弹幕|r；若你没赢，该角色可以视为对你使用了一张|G弹幕|r。'

    custom_ray = True

    def clickable(game):
        if limit1_skill_used('incite_tag'):
            return False

        return my_turn()

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
                src.ui_meta.name,
                tgt.ui_meta.name,
            )
        else:
            return u'|G【%s】|r一脸坏笑，对|G【%s】|r说：“你知道吗，|G【%s】|r刚才看了你的胖次，蓝白条，赞！”' % (
                src.ui_meta.name,
                tgt.ui_meta.name,
                victim.ui_meta.name,
            )

    def sound_effect(act):
        return random.choice([
            'thb-cv-seija_incite1',
            'thb-cv-seija_incite2',
        ])


class InciteAction:
    # choose_option
    choose_option_buttons = ((u'使用', True), (u'不使用', False))

    def ray(act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]

    def choose_option_prompt(act):
        return u'你要对【%s】使用【弹幕】吗？' % act.source.ui_meta.name


class Reversal:
    # Skill
    name = u'逆转'
    description = u'当你受到一名其他角色使用的|G弹幕|r效果时，你可以摸一张牌，然后若你的手牌数大于其手牌数，你将此|G弹幕|r视为|G弹幕战|r'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ReversalDuel:
    name = u'逆转'

    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r：“你敢打我脸，我就敢打回去！”' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-seija_reversal'


class ReversalHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【逆转】吗？'


class Seija:
    # Character
    name        = u'鬼人正邪'
    title       = u'逆袭的天邪鬼'
    illustrator = u'霏茶'
    cv          = u'北斗夜'

    port_image        = u'thb-portrait-seija'
    figure_image      = u'thb-figure-seija'
    miss_sound_effect = u'thb-cv-seija_miss'
