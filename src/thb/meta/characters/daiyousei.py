# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid

# -- code --


@ui_meta(characters.daiyousei.Daiyousei)
class Daiyousei:
    # Character
    name        = '大妖精'
    title       = '全身萌点的保姆'
    illustrator = '渚FUN'
    cv          = '简翎'

    port_image        = 'thb-portrait-daiyousei'
    figure_image      = 'thb-figure-daiyousei'
    miss_sound_effect = 'thb-cv-daiyousei_miss'


@ui_meta(characters.daiyousei.DaiyouseiKOF)
class DaiyouseiKOF:
    # Character
    name        = '大妖精'
    title       = '全身萌点的保姆'
    illustrator = '渚FUN'
    cv          = '简翎'

    port_image        = 'thb-portrait-daiyousei'
    figure_image      = 'thb-figure-daiyousei'
    miss_sound_effect = 'thb-cv-daiyousei_miss'

    notes = '|RKOF修正角色|r'


@ui_meta(characters.daiyousei.Support)
class Support:
    # Skill
    name = '支援'
    description = '出牌阶段，你可将任意张牌交给其他角色，此阶段你给出的牌首次达到三张时，你回复1点体力。'

    def clickable(self, game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards or me.equips):
            return True

        return False

    def is_action_valid(self, g, cl, target_list):
        cl = cl[0].associated_cards
        if not cl: return (False, '请选择要给出的牌')
        me = g.me
        allcards = list(me.cards) + list(me.showncards) + list(me.equips)
        if any(
            c not in allcards
            for c in cl
        ): return (False, '你只能选择手牌与装备牌！')
        if len(target_list) != 1: return (False, '请选择1名玩家')
        return (True, '加油！')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return '|G【%s】|r发动了|G支援|r技能，将%d张牌交给了|G【%s】|r' % (
            act.source.ui_meta.name,
            len(act.card.associated_cards),
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-daiyousei_support'


@ui_meta(characters.daiyousei.SupportKOF)
class SupportKOF:
    # Skill
    name = '支援'
    description = '你死亡时，你可以将你的所有牌移出游戏，并令下一名登场的角色获得这些牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.daiyousei.SupportKOFAction)
class SupportKOFAction:

    def effect_string_before(self, act):
        return '|G【%s】|r发动了|G支援|r技能，将所有的牌转移给下一个出场角色。' % (
            act.target.ui_meta.name
        )


@ui_meta(characters.daiyousei.SupportKOFHandler)
class SupportKOFHandler:
    choose_option_prompt = '你要发动【支援】，将所有牌转移给下一名出场角色吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(characters.daiyousei.Moe)
class Moe:
    # Skill
    name = '卖萌'
    description = '|B锁定技|r，摸牌阶段你额外摸X张牌（X为你已损失的体力值）。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.daiyousei.MoeDrawCard)
class MoeDrawCard:
    def effect_string(self, act):
        return '|G【%s】|r用手扯开脸颊，向大家做了一个夸张的笑脸，摸了%d张牌跑开了' % (
            act.target.ui_meta.name,
            act.amount,
        )

    def sound_effect(self, act):
        return 'thb-cv-daiyousei_moe'

# ----------
