# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.momiji)


class Momiji:
    # Character
    char_name = u'犬走椛'
    port_image = 'thb-portrait-momiji'
    miss_sound_effect = 'thb-cv-momiji_miss'
    description = (
        u'|DB山中的千里眼 犬走椛 体力：4|r\n\n'
        u'|G哨戒|r：当一名其他角色（记作A）使用弹幕对另一角色（记作B）造成伤害时，若A在你的攻击范围内，你可以对A使用一张【弹幕】，或将一张梅花牌当【弹幕】对A使用。此【弹幕】造成伤害时，你可以防止此伤害，并且令B此次受到的伤害-1。\n\n'
        u'|G千里眼|r：|B锁定技|r，你与其他角色计算距离时始终-1。\n\n'
        u'|DB（画师：Danbooru post 621700，CV：简翎）|r'
    )


class MomijiKOF:
    # Character
    char_name = u'犬走椛'
    port_image = 'thb-portrait-momiji'
    miss_sound_effect = 'thb-cv-momiji_miss'
    description = (
        u'|DB山中的千里眼 犬走椛 体力：4|r\n\n'
        u'|G哨戒|r：当一名其他角色（记作A）使用弹幕对另一角色（记作B）造成伤害时，若A在你的攻击范围内，你可以对A使用一张【弹幕】，或将一张梅花牌当【弹幕】对A使用。此【弹幕】造成伤害时，你可以防止此伤害，并且令B此次受到的伤害-1。\n\n'
        u'|G千里眼|r：|B锁定技|r，对手获得牌时，所获得的第一张牌进入明牌区。\n\n'
        u'|RKOF修正角色|r\n\n'
        u'|DB（画师：Danbooru post 621700，CV：简翎）|r'
    )


class Sentry:
    # Skill
    name = u'哨戒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SharpEye:
    # Skill
    name = u'千里眼'
    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SharpEyeKOF:
    # Skill
    name = u'千里眼'
    no_display = False
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SharpEyeKOFAction:

    def effect_string_before(act):
        return u'|G【%s】|r一撅屁股，|G【%s】|r就看到了她穿了什么牌子的胖次。' % (
            act.target.ui_meta.char_name,
            act.source.ui_meta.char_name,
        )


class SentryAttack:
    # Skill
    name = u'哨戒'

    def sound_effect(act):
        return random.choice([
            'thb-cv-momiji_sentry1',
            'thb-cv-momiji_sentry2',
        ])


class SentryHandler:
    # choose_option meta
    choose_option_buttons = ((u'保护', True), (u'伤害', False))
    choose_option_prompt = u'你希望发动的效果？'

    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'吃我大弹幕啦！(对%s发动哨戒)' % act.target.ui_meta.char_name)
        else:
            return (False, u'请选择一张弹幕或者草花色牌发动哨戒(对%s)' % act.target.ui_meta.char_name)
