# -*- coding: utf-8 -*-

import random

from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, meta_property
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.kaguya)


class Kaguya:
    # Character
    char_name = u'蓬莱山辉夜'
    port_image = gres.kaguya_port
    miss_sound_effect = gres.cv.kaguya_miss
    description = (
        u'|DB永远的公主殿下 蓬莱山辉夜 体力：3|r\n\n'
        u'|G难题|r：一名角色每次令你回复一点体力时，你可以令该角色摸一张牌；你每受到一次伤害后，可令伤害来源交给你一张方片牌，否则其失去一点体力。\n\n'
        u'|G永夜|r：在你的回合外，当一名角色的一张红色基本牌因使用进入弃牌堆时，你可以将一张红色基本牌/装备牌置于该角色的判定区视为【封魔阵】。\n\n'
        u'|DB（画师：Pixiv UID 334389，CV：shourei小N）|r'
    )


class Dilemma:
    # Skill
    name = u'难题'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DilemmaDamageAction:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'交出一张方片牌')
        else:
            return (False, u'请选择交出一张方片牌（否则失去一点体力）')

    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r发动了|G难题|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )

    def effect_string(act):
        if act.peer_action == 'card':
            return u'|G【%s】|r给了|G【%s】|r一张牌。' % (
                act.target.ui_meta.char_name,
                act.source.ui_meta.char_name
            )
        # elif act.peer_action == 'life':
        #     <handled by LifeLost>

    def sound_effect(act):
        return random.choice([
            gres.cv.kaguya_dilemma1,
            gres.cv.kaguya_dilemma2,
        ])


class DilemmaHealAction:
    def effect_string(act):
        return u'|G【%s】|r发动了|G难题|r，|G【%s】|r摸了一张牌。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return random.choice([
            gres.cv.kaguya_dilemma1,
            gres.cv.kaguya_dilemma2,
        ])


class DilemmaHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))

    def choose_option_prompt(act):
        _type = {
            'positive': u'正面效果',
            'negative': u'负面效果'
        }.get(act.dilemma_type, u'WTF?!')
        return u'你要发动【难题】吗（%s）？' % _type


class ImperishableNight:
    # Skill
    name = u'永夜'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

    @meta_property
    def image(c):
        return c.associated_cards[0].ui_meta.image

    tag_anim = lambda c: gres.tag_sealarray
    description = (
        u'|G【蓬莱山辉夜】|r的技能产生的【封魔阵】'
    )

    def effect_string(act):
        return u'|G【%s】|r对|G【%s】|r使用了|G永夜|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name
        )

    def sound_effect(act):
        return gres.cv.kaguya_inight


class ImperishableNightHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))

    def choose_option_prompt(act):
        prompt = u'你要发动【永夜】吗（对%s）？'
        return prompt % act.target.ui_meta.char_name

    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'陷入永夜吧！')
        else:
            return (False, u'请选择一张红色的基本牌或装备牌')
