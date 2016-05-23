# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import actions, cards, characters
from thb.ui.ui_meta.common import build_handcard, card_desc, current_initiator, gen_metafunc
from thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.momiji)


class Momiji:
    # Character
    char_name = u'犬走椛'
    port_image = 'thb-portrait-momiji'
    figure_image = 'thb-figure-momiji'
    miss_sound_effect = 'thb-cv-momiji_miss'
    description = (
        u'|DB山中的千里眼 犬走椛 体力：4|r\n\n'
        u'|G哨戒|r：一名你攻击范围内的其他角色的出牌阶段开始时，你可以对其使用一张|G弹幕|r。你使用的|G弹幕|r或|G弹幕战|r造成伤害后，你可以观看其手牌，并将其中任意数量的|G弹幕|r和符卡牌移出游戏，直到该角色的回合结束阶段，其获得这些被移出游戏的牌。\n\n'
        u'|G坚盾|r：若你的手牌数大于你的当前体力值，你可以将一张黑色牌当|G弹幕|r使用或打出。否则你可以将一张红色牌当|G擦弹|r使用或打出。\n\n'
        u'|DB（画师：和茶，CV：简翎）|r'
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


class SolidShieldAttack:
    # Skill
    name = u'坚盾(弹)'

    def clickable(g):
        try:
            me = g.me

            if not len(me.cards) + len(me.showncards) > me.life:
                return False

            initiator = current_initiator()
            if isinstance(initiator, actions.ActionStage):
                return True

            if initiator.cond([build_handcard(cards.AttackCard)]):
                return True
        except:
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        cl = skill.associated_cards
        from thb.cards import Card
        if len(cl) != 1 or not (cl[0].color == Card.BLACK):
            return (False, u'请选择一张黑色牌！')
        return (True, u'这句貌似看不到……？')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        src = act.source
        return (
            u'|G【%s】|r发动了|G坚盾|r，将%s视为了|G弹幕|r。'
        ) % (
            src.ui_meta.char_name,
            card_desc(act.card.associated_cards[0]),
        )

    def sound_effect(act):
        from thb.cards import AttackCard
        return AttackCard.ui_meta.sound_effect(act)


class SolidShieldGraze:
    # Skill
    name = u'坚盾(擦)'

    def clickable(g):
        try:
            me = g.me
            if not len(me.cards) + len(me.showncards) <= me.life:
                return False

            initiator = current_initiator()
            if isinstance(initiator, actions.ActionStage):
                return True

            if initiator.cond([build_handcard(cards.GrazeCard)]):
                return True
        except:
            pass

        return False

    def is_complete(g, cl):
        skill = cl[0]
        cl = skill.associated_cards
        from thb.cards import Card
        if len(cl) != 1 or not (cl[0].color == Card.RED):
            return (False, u'请选择一张红色牌！')
        return (True, u'这句貌似看不到……？')

    def is_action_valid(g, cl, target_list, is_complete=is_complete):
        skill = cl[0]
        rst, reason = is_complete(g, cl)
        if not rst:
            return (rst, reason)
        else:
            return skill.treat_as.ui_meta.is_action_valid(g, [skill], target_list)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        src = act.source
        return (
            u'|G【%s】|r发动了|G坚盾|r，将%s视为了|G擦弹|r。'
        ) % (
            src.ui_meta.char_name,
            card_desc(act.card.associated_cards[0]),
        )

    def sound_effect(act):
        from thb.cards import GrazeCard
        return GrazeCard.ui_meta.sound_effect(act)


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
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你希望【哨戒】效果？'

    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'吃我大弹幕啦！(对%s发动哨戒)' % act.target.ui_meta.char_name)
        else:
            return (False, u'哨戒：请选择一张弹幕发动哨戒(对%s)' % act.target.ui_meta.char_name)
