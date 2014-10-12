# -*- coding: utf-8 -*-

from gamepack.thb import characters
from gamepack.thb.actions import ttags
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.sanae)


class Sanae:
    # Character
    char_name = u'东风谷早苗'
    port_image = gres.sanae_port
    miss_sound_effect = gres.cv.sanae_miss
    description = (
        u'|DB常识满满的现人神 东风谷早苗 体力：3|r\n\n'
        u'|G奇迹|r：出牌阶段，你可以弃置X张牌并摸一张牌。若你以此法弃置的手牌数累计大于3张，你可以令一名角色回复一点体力。（X为你本回合发动|G奇迹|r的次数）\n'
        u'|B|R>> |r当你回合内第一次使用|G奇迹|r时，X为1，第二次为2，以此类推。\n\n'
        u'|G信仰|r：出牌阶段限一次，你可以令至多两名其他角色各交给你一张手牌，然后你交给其各一张牌。\n\n'
        u'|DB（画师：Pixiv ID 37694260，CV：VV）|r'
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
        me = g.me
        expected = ttags(me)['miracle_times'] + 1
        if len(cards) != expected:
            return (False, u'奇迹：请选择%d张牌！' % expected)

        return (True, u'奇迹是存在的！')

    def sound_effect(act):
        return gres.cv.sanae_miracle


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
        return gres.cv.sanae_faith


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
