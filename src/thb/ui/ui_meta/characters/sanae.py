# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.sanae)


class Sanae:
    # Character
    char_name = u'东风谷早苗'
    port_image = 'thb-portrait-sanae'
    figure_image = 'thb-figure-sanae'
    miss_sound_effect = 'thb-cv-sanae_miss'
    description = (
        u'|DB常识满满的现人神 东风谷早苗 体力：3|r\n\n'
        u'|G奇迹|r：出牌阶段，你可以弃置X张牌并摸一张牌。若X为3，你可以令一名角色回复一点体力。\n'
        u'|B|R>> |rX为你本回合发动|G奇迹|r的次数，当你回合内第一次使用|G奇迹|r时，X为1，第二次为2，以此类推。\n\n'
        u'|G信仰|r：出牌阶段限一次，你可以令至多两名其他角色各交给你一张手牌，然后你交给其各一张牌。\n\n'
        u'|G神裔|r：当你成为群体符卡的目标后，你可以重铸一张牌并跳过此次结算。\n\n'
        u'|DB（画师：小D@星の妄想乡，CV：VV）|r'
    )


class SanaeKOF:
    # Character
    char_name = u'东风谷早苗'
    port_image = 'thb-portrait-sanae'
    figure_image = 'thb-figure-sanae'
    miss_sound_effect = 'thb-cv-sanae_miss'
    description = (
        u'|DB常识满满的现人神 东风谷早苗 体力：3|r\n\n'
        u'|G奇迹|r：出牌阶段，你可以弃置X张牌并摸一张牌。若X为3，你可以令一名角色回复一点体力。\n'
        u'|B|R>> |rX为你本回合发动|G奇迹|r的次数，当你回合内第一次使用|G奇迹|r时，X为1，第二次为2，以此类推。\n\n'
        u'|G信仰|r：|B锁定技|r，你的对手于自己的出牌阶段获得牌后，你摸一张牌。\n\n'
        u'|G神裔|r：当你成为群体符卡的目标后，你可以摸一张牌或跳过此次结算。\n\n'
        u'|RKOF修正角色|r\n\n'
        u'|DB（画师：小D@星の妄想乡，CV：VV）|r'
    )


class Miracle:
    name = u'奇迹'

    def clickable(g):
        return my_turn()

    def effect_string(act):
        return u'|G【%s】|r发动了|G奇迹|r，弃置了%d张牌' % (
            act.source.ui_meta.char_name,
            len(act.card.associated_cards),
        )

    def is_action_valid(g, cl, tl):
        cards = cl[0].associated_cards

        expected = ttags(g.me)['miracle_times'] + 1
        if len(cards) != expected:
            return (False, u'奇迹：请选择%d张牌！' % expected)

        return (True, u'奇迹是存在的！')

    def sound_effect(act):
        return 'thb-cv-sanae_miracle'


class MiracleAction:

    def target(pl):
        if not pl:
            return (False, u'奇迹：请选择1名受伤的玩家，回复一点体力（否则不发动）')

        return (True, u'奇迹：回复1点体力')


class SanaeFaith:
    name = u'信仰'

    def clickable(g):
        return my_turn() and not ttags(g.me)['faith']

    def effect_string(act):
        return u'|G【%s】|r的|G信仰|r大作战！向%s收集了信仰！' % (
            act.source.ui_meta.char_name,
            u'、'.join([u'|G【%s】|r' % p.ui_meta.char_name for p in act.target_list]),
        )

    def is_action_valid(g, cl, tl):
        cards = cl[0].associated_cards
        if cards:
            return (False, u'请不要选择牌！')

        return (True, u'团队需要信仰！')

    def sound_effect(act):
        return 'thb-cv-sanae_faith'


class SanaeFaithKOF:
    name = u'信仰'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SanaeFaithKOFDrawCards:
    def effect_string(act):
        return u'|G【%s】|r向牌堆收集了1点|G信仰|r。' % (
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-sanae_faith'


class SanaeFaithCollectCardAction:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'信仰：交出这一张手牌，然后收回一张牌')
        else:
            return (False, u'信仰：请交出一张手牌')


class SanaeFaithReturnCardAction:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'信仰：将这一张牌返还给%s' % act.target.ui_meta.char_name)
        else:
            return (False, u'信仰：选择一张牌返还给%s' % act.target.ui_meta.char_name)


class GodDescendant:
    name = u'神裔'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class GodDescendantHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'神裔：重铸并跳过结算')
        else:
            return (False, u'神裔：请选择要重铸的牌并跳过结算（否则不发动）')


class GodDescendantAction:

    def effect_string(act):
        return u'|G【%s】|r发动了|G神裔|r，重铸了一张牌并跳过了结算。' % (
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return random.choice([
            'thb-cv-sanae_goddescendant1',
            'thb-cv-sanae_goddescendant2',
        ])
