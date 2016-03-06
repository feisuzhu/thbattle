# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.daiyousei)


class Daiyousei:
    # Character
    char_name = u'大妖精'
    port_image = 'thb-portrait-daiyousei'
    figure_image = 'thb-figure-daiyousei'
    miss_sound_effect = 'thb-cv-daiyousei_miss'
    description = (
        u'|DB全身萌点的保姆 大妖精 体力：3|r\n\n'
        u'|G支援|r：出牌阶段，你可以将任意数量的牌交给其他角色，若此阶段你给出的牌张数达到3张或更多时，你回复1点体力。\n\n'
        u'|G卖萌|r：|B锁定技|r，摸牌阶段你额外摸X张牌（X为你已损失的体力值）。\n\n'
        u'|DB（画师：渚FUN，CV：简翎）|r'
    )


class DaiyouseiKOF:
    # Character
    char_name = u'大妖精'
    port_image = 'thb-portrait-daiyousei'
    figure_image = 'thb-figure-daiyousei'
    miss_sound_effect = 'thb-cv-daiyousei_miss'
    description = (
        u'|DB全身萌点的保姆 大妖精 体力：3|r\n\n'
        u'|G支援|r：你死亡时，可以将你的全部卡牌移出游戏，并使下一名登场的角色获得这些牌。\n\n'
        u'|G卖萌|r：|B锁定技|r，摸牌阶段你额外摸X张牌（X为你已损失的体力值）。\n\n'
        u'|RKOF修正角色|r\n\n'
        u'|DB（画师：渚FUN，CV：简翎）|r'
    )


class Support:
    # Skill
    name = u'支援'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(g, cl, target_list):
        cl = cl[0].associated_cards
        if not cl: return (False, u'请选择要给出的牌')
        me = g.me
        allcards = list(me.cards) + list(me.showncards) + list(me.equips)
        if any(
            c not in allcards
            for c in cl
        ): return (False, u'你只能选择手牌与装备牌！')
        if len(target_list) != 1: return (False, u'请选择1名玩家')
        return (True, u'加油！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r发动了|G支援|r技能，将%d张牌交给了|G【%s】|r' % (
            act.source.ui_meta.char_name,
            len(act.card.associated_cards),
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-daiyousei_support'


class SupportKOF:
    # Skill
    name = u'支援'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SupportKOFAction:

    def effect_string_before(act):
        return u'|G【%s】|r发动了|G支援|r技能，将所有的牌转移给下一个出场角色。' % (
            act.target.ui_meta.char_name
        )


class SupportKOFHandler:
    choose_option_prompt = u'你要发动【支援】，将所有牌转移给下一名出场角色吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class Moe:
    # Skill
    name = u'卖萌'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MoeDrawCard:
    def effect_string(act):
        return u'|G【%s】|r用手扯开脸颊，向大家做了一个夸张的笑脸，摸了%d张牌跑开了' % (
            act.target.ui_meta.char_name,
            act.amount,
        )

    def sound_effect(act):
        return 'thb-cv-daiyousei_moe'

# ----------
