# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import cards, thbidentity
from thb.actions import ttags
from thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(thbidentity)


class THBattleIdentity:
    name = u'8人身份场'
    logo = 'thb-modelogo-8id'
    description = (
        u'|R游戏人数|r：8人\n'
        u'\n'
        u'|R身份分配|r：1|!RBOSS|r、2|!O道中|r、1|!G黑幕|r、4|!B城管|r\n'
        u'\n'
        u'|!RBOSS|r：|!RBOSS|r的体力上限+1。游戏开局时展示身份。胜利条件为击坠所有|!B城管|r以及|!G黑幕|r。\n'
        u'\n'
        u'|!O道中|r：胜利条件为击坠所有|!B城管|r以及|!G黑幕|r。\n'
        u'\n'
        u'|!B城管|r：胜利条件为击坠|!RBOSS|r。当|!B城管|rMISS时，击坠者摸3张牌。\n'
        u'\n'
        u'|!G黑幕|r：胜利条件为在|!B城管|r全部MISS的状况下击坠|!RBOSS|r。\n'
        u'|B|R>> |r|R双黑幕模式|r下胜利条件条件是除了|!RBOSS|r的其他人全部MISS的情况下击坠|!RBOSS|r。\n'
        u'\n'
        u'玩家的身份会在MISS后公开。|!RBOSS|r的身份会在开局的时候公开。'
    )
    params_disp = {
        'double_curtain': {
            'desc': u'双黑幕模式',
            'options': [
                (u'双黑幕', True),
                (u'正常', False),
            ],
        },
    }

    def ui_class():
        from thb.ui.view import THBattleIdentityUI
        return THBattleIdentityUI

    T = thbidentity.Identity.TYPE
    identity_table = {
        T.HIDDEN:     u'？',
        T.ATTACKER:   u'城管',
        T.BOSS:       u'BOSS',
        T.ACCOMPLICE: u'道中',
        T.CURTAIN:    u'黑幕',
    }

    identity_color = {
        T.HIDDEN:     u'blue',
        T.ATTACKER:   u'blue',
        T.BOSS:       u'red',
        T.ACCOMPLICE: u'orange',
        T.CURTAIN:    u'green',
    }

    IdentityType = T
    del T


class AssistedAttack:
    # Skill
    name = u'激将'

    def clickable(game):
        me = game.me
        if not my_turn():
            return False

        if ttags(me)['assisted_attack_disable']:
            return False

        return True

    def is_action_valid(g, cl, tl):
        s = cl[0]
        cl = s.associated_cards
        if len(cl):
            return (False, u'请不要选择牌！')

        return cards.AttackCard.ui_meta.is_action_valid(g, [s], tl)

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r。发动了|G激将|r标是|G【%s】|r。'
        ) % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class AssistedUseAttackAction:
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'帮%s出弹幕' % act.target.ui_meta.char_name)
        else:
            return (False, u'激将：请选择一张弹幕（帮%s出）' % act.target.ui_meta.char_name)


class AssistedAttackAction:
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'对%s出弹幕' % act.target.ui_meta.char_name)
        else:
            return (False, u'激将：请选择一张弹幕（对%s出）' % act.target.ui_meta.char_name)


class AssistedAttackHandler:
    choose_option_prompt = u'你要发动【激将】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class AssistedGraze:
    # Skill
    name = u'护驾'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AssistedUseGrazeAction:
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'帮%s出擦弹' % act.target.ui_meta.char_name)
        else:
            return (False, u'护驾：请选择一张擦弹（帮%s出）' % act.target.ui_meta.char_name)


class AssistedGrazeHandler:
    choose_option_prompt = u'你要发动【护驾】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class AssistedHealAction:
    def effect_string_before(act):
        return u'|G【%s】|r发动了|G救援|r' % (
            act.source.ui_meta.char_name,
        )


class AssistedHealHandler:
    choose_option_prompt = u'你要发动【救援】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class AssistedHeal:
    # Skill
    name = u'救援'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ExtraCardSlot:
    # Skill
    name = u'血裔'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ChooseBossSkillAction:
    choose_option_prompt = u'请选择协力技：'

    def choose_option_buttons(act):
        l = act.boss_skills
        return [(i.ui_meta.name, i.__name__) for i in l]

    def effect_string(act):
        return u'|G【%s】|r选择了|G%s|r作为协力技' % (
            act.target.ui_meta.char_name,
            act.skill_chosen.ui_meta.name,
        )
