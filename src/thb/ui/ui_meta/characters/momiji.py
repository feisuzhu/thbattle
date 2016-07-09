# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.momiji)


class Momiji:
    # Character
    char_name = u'犬走椛'
    port_image = 'thb-portrait-momiji'
    figure_image = 'thb-figure-momiji'
    miss_sound_effect = 'thb-cv-momiji_miss'
    description = (
        u'|DB山中的千里眼 犬走椛 体力：4|r\n'
        u'\n'
        u'|G缴械|r：你使用的|G弹幕|r或|G弹幕战|r造成伤害后，你可以观看其手牌，并将其中任意数量的|G弹幕|r和符卡牌移出游戏，直到该角色的回合结束阶段，其获得这些被移出游戏的牌。\n'
        u'\n'
        u'|G哨戒|r：一名你攻击范围内的其他角色的出牌阶段开始时，你可以对其使用一张|G弹幕|r。\n'
        u'\n'
        # u'|G千里眼|r：|B锁定技|r，若你在一名其他角色的攻击内，则该角色视为在你攻击范围内。\n'
        # u'\n'
        u'|G断噬|r：你距离1以内的角色成为另一名其他角色使用的弹幕或非延时符卡的唯一目标时，若该卡牌为其出牌阶段使用的第一张卡牌，你可以令其无效并将其移出游戏。\n'
        u'\n'
        u'|DB（画师：和茶，CV：简翎）|r'
    )


class Sentry:
    # Skill
    name = u'哨戒'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Telegnosis:
    # Skill
    name = u'千里眼'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class Disarm:
    # Skill
    name = u'缴械'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SentryAttack:
    # Skill
    name = u'哨戒'

    def sound_effect(act):
        return random.choice([
            'thb-cv-momiji_sentry1',
            'thb-cv-momiji_sentry2',
        ])


class DisarmHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你希望发动【缴械】吗？'


class SentryHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'吃我大弹幕啦！(对%s发动哨戒)' % act.target.ui_meta.char_name)
        else:
            return (False, u'哨戒：请选择一张弹幕发动哨戒(对%s)' % act.target.ui_meta.char_name)


class RabiesBiteHandler:
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你希望发动【断噬】吗？'


class RabiesBiteAction:
    def effect_string_before(act):
        return u'“嗷~~~~！”|G【%s】|r突然冲了出来，吓的|G【%s】|r手里的%s都掉在地上了。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
            card_desc(act.action.card),
        )


class RabiesBite:
    # Skill
    name = u'断噬'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid
