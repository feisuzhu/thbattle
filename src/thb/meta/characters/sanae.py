# -*- coding: utf-8 -*-


# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.meta.common import ui_meta, my_turn, passive_clickable, passive_is_action_valid


# -- code --


@ui_meta(characters.sanae.Sanae)
class Sanae:
    # Character
    name        = '东风谷早苗'
    title       = '常识满满的现人神'
    illustrator = '小D@星の妄想乡'
    cv          = 'VV'

    port_image        = 'thb-portrait-sanae'
    figure_image      = 'thb-figure-sanae'
    miss_sound_effect = 'thb-cv-sanae_miss'


@ui_meta(characters.sanae.SanaeKOF)
class SanaeKOF:
    # Character
    name        = '东风谷早苗'
    title       = '常识满满的现人神'
    illustrator = '小D@星の妄想乡'
    cv          = 'VV'

    port_image        = 'thb-portrait-sanae'
    figure_image      = 'thb-figure-sanae'
    miss_sound_effect = 'thb-cv-sanae_miss'

    notes = '|RKOF修正角色|r'


@ui_meta(characters.sanae.Miracle)
class Miracle:
    name = '奇迹'
    description = '出牌阶段，你可以弃置X张牌并摸一张牌；若X为3，你可以令一名角色回复1点体力。（X为你此阶段使用奇迹的次数）'

    def clickable(self, g):
        return my_turn()

    def effect_string(self, act):
        return '|G【%s】|r发动了|G奇迹|r，弃置了%d张牌' % (
            act.source.ui_meta.name,
            len(act.card.associated_cards),
        )

    def is_action_valid(self, g, cl, tl):
        cards = cl[0].associated_cards

        expected = ttags(g.me)['miracle_times'] + 1
        if len(cards) != expected:
            return (False, '奇迹：请选择%d张牌！' % expected)

        return (True, '奇迹是存在的！')

    def sound_effect(self, act):
        return 'thb-cv-sanae_miracle'


@ui_meta(characters.sanae.MiracleAction)
class MiracleAction:

    def target(self, pl):
        if not pl:
            return (False, '奇迹：请选择1名受伤的玩家，回复一点体力（否则不发动）')

        return (True, '奇迹：回复1点体力')


@ui_meta(characters.sanae.SanaeFaith)
class SanaeFaith:
    name = '信仰'
    description = '出牌阶段限一次，你可以令至多两名其他角色各交给你一张手牌，然后你交给其各一张牌。'

    def clickable(self, g):
        return my_turn() and not ttags(g.me)['faith']

    def effect_string(self, act):
        return '|G【%s】|r的|G信仰|r大作战！向%s收集了信仰！' % (
            act.source.ui_meta.name,
            '、'.join(['|G【%s】|r' % p.ui_meta.name for p in act.target_list]),
        )

    def is_action_valid(self, g, cl, tl):
        cards = cl[0].associated_cards
        if cards:
            return (False, '请不要选择牌！')

        return (True, '团队需要信仰！')

    def sound_effect(self, act):
        return 'thb-cv-sanae_faith'


@ui_meta(characters.sanae.SanaeFaithKOF)
class SanaeFaithKOF:
    name = '信仰'
    description = '|B锁定技|r，对方的出牌阶段，每当其获得牌时，你摸一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.sanae.SanaeFaithKOFDrawCards)
class SanaeFaithKOFDrawCards:
    def effect_string(self, act):
        return '|G【%s】|r向牌堆收集了1点|G信仰|r。' % (
            act.source.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-sanae_faith'


@ui_meta(characters.sanae.SanaeFaithCollectCardAction)
class SanaeFaithCollectCardAction:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '信仰：交出这一张手牌，然后收回一张牌')
        else:
            return (False, '信仰：请交出一张手牌')


@ui_meta(characters.sanae.SanaeFaithReturnCardAction)
class SanaeFaithReturnCardAction:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '信仰：将这一张牌返还给%s' % act.target.ui_meta.name)
        else:
            return (False, '信仰：选择一张牌返还给%s' % act.target.ui_meta.name)


@ui_meta(characters.sanae.GodDescendant)
class GodDescendant:
    name = '神裔'
    description = '每当你成为群体符卡的目标后，你可以重铸一张牌并跳过此次结算。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.sanae.GodDescendantAction)
class GodDescendantAction:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '神裔：重铸并跳过结算')
        else:
            return (False, '神裔：请选择要重铸的牌并跳过结算（否则不发动）')


@ui_meta(characters.sanae.GodDescendantEffect)
class GodDescendantEffect:

    def effect_string_before(self, act):
        return '|G【%s】|r发动了|G神裔|r，重铸了一张牌并跳过了结算。' % (
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-sanae_goddescendant1',
            'thb-cv-sanae_goddescendant2',
        ])
