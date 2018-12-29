# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thbrole
from thb.actions import ttags
from thb.cards.classes import AttackCard
from thb.meta.common import card_desc, my_turn, passive_clickable, passive_is_action_valid
from thb.meta.common import ui_meta


# -- code --
@ui_meta(thbrole.THBattleRole)
class THBattleRole:
    name = '8人身份场'
    logo = 'thb-modelogo-8id'
    description = (
        '|R游戏人数|r：8人\n'
        '\n'
        '|R身份分配|r：1|!RBOSS|r、2|!O道中|r、1|!G黑幕|r、4|!B城管|r\n'
        '\n'
        '|!RBOSS|r：|!RBOSS|r的体力上限+1。游戏开局时展示身份，并获得BOSS技。胜利条件为击坠所有|!B城管|r以及|!G黑幕|r。\n'
        '\n'
        '|!O道中|r：胜利条件为击坠所有|!B城管|r以及|!G黑幕|r。\n'
        '\n'
        '|!B城管|r：胜利条件为击坠|!RBOSS|r。当|!B城管|r被击坠时，击坠者摸3张牌。\n'
        '\n'
        '|!G黑幕|r：胜利条件为在|!B城管|r全部被击坠的状况下击坠|!RBOSS|r。\n'
        '|B|R>> |r|R双黑幕模式|r下胜利条件条件是除了|!RBOSS|r的其他人全部被击坠的情况下击坠|!RBOSS|r。\n'
        '\n'
        '玩家的身份会在被击坠后公开。|!RBOSS|r的身份会在开局的时候公开。\n'
        '\n'
        '|RBOSS技：|r'
        '|!RBOSS|r身份的玩家在开场会获得BOSS技。'
        '\n'
        '某些角色在在设定上有专属的BOSS技，开局时会额外获得\n'
        '没有专属BOSS技的角色会在如下几个通用BOSS技中选择一个获得：\n'
        '\n'
        '|G同仇|r：当你需要使用或打出一张|G弹幕|r时，其他玩家可以代替你使用或打出一张|G弹幕|r\n'
        '\n'
        '|G协力|r：当你需要使用或打出一张|G擦弹|r时，其他玩家可以代替你使用或打出一张|G擦弹|r\n'
        '\n'
        '|G牺牲|r：当你于濒死状态下，被一名角色使用|G麻薯|r而回复体力至1后，其可以失去一点体力，令你额外回复一点体力\n'
        '\n'
        '|G应援|r：锁定技，每有一名道中存活，你的手牌上限便+1\n'
    ).strip()

    params_disp = {
        'double_curtain': {
            'desc': '双黑幕模式',
            'options': [
                ('双黑幕', True),
                ('正常', False),
            ],
        },
    }

    roles_disp = {
        thbrole.THBRoleRole.HIDDEN:     '？',
        thbrole.THBRoleRole.BOSS:       'BOSS',
        thbrole.THBRoleRole.ACCOMPLICE: '道中',
        thbrole.THBRoleRole.ATTACKER:   '城管',
        thbrole.THBRoleRole.CURTAIN:    '黑幕',
    }


@ui_meta(thbrole.AssistedAttack)
class AssistedAttack:
    # Skill
    name = '同仇'
    description = '当你需要使用或打出一张|G弹幕|r时，其他玩家可以代替你使用或打出一张|G弹幕|r'

    def clickable(self, g):
        me = g.me
        if not my_turn():
            return False

        if ttags(me)['assisted_attack_disable']:
            return False

        return True

    def is_action_valid(self, g, cl, tl):
        s = cl[0]
        cl = s.associated_cards
        if len(cl):
            return (False, '请不要选择牌！')

        return AttackCard.ui_meta.is_action_valid(g, [s], tl)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return (
            '|G【%s】|r发动了|G同仇|r，目标是|G【%s】|r。'
        ) % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


@ui_meta(thbrole.AssistedUseAction)
class AssistedUseAction:
    def choose_option_prompt(self, act):
        return '你要帮BOSS出【%s】吗？' % (
            act.their_afc_action.card_cls.ui_meta.name
        )

    choose_option_buttons = (('帮BOSS', True), ('不关我事', False))


@ui_meta(thbrole.AssistedAttackAction)
class AssistedAttackAction:
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '帮BOSS对%s出弹幕' % act.target.ui_meta.name)
        else:
            return (False, '同仇：请选择一张弹幕（对%s出）' % act.target.ui_meta.name)


@ui_meta(thbrole.AssistedAttackCard)
class AssistedAttackCard:
    def effect_string(self, act):
        s = act.card
        c = s.associated_cards[0]
        return '|G【%s】|r响应了|G同仇|r，使用了|G%s|r' % (
            c.resides_in.owner.ui_meta.name,
            card_desc(c),
        )


@ui_meta(thbrole.AssistedAttackHandler)
class AssistedAttackHandler:
    choose_option_prompt = '你要发动【同仇】吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(thbrole.AssistedGraze)
class AssistedGraze:
    # Skill
    name = '协力'
    description = '当你需要使用或打出一张|G擦弹|r时，其他玩家可以代替你使用或打出一张|G擦弹|r'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(thbrole.AssistedGrazeHandler)
class AssistedGrazeHandler:
    choose_option_prompt = '你要发动【协力】吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(thbrole.AssistedHealAction)
class AssistedHealAction:
    def effect_string_before(self, act):
        return '|G【%s】|r发动了|G牺牲|r' % (
            act.source.ui_meta.name,
        )


@ui_meta(thbrole.AssistedHealHandler)
class AssistedHealHandler:
    choose_option_prompt = '你要发动【牺牲】吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(thbrole.AssistedHeal)
class AssistedHeal:
    # Skill
    name = '牺牲'
    description = '当你于濒死状态下，被一名角色使用|G麻薯|r而回复体力至1后，其可以失去一点体力，令你额外回复一点体力'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(thbrole.ExtraCardSlot)
class ExtraCardSlot:
    # Skill
    name = '应援'
    description = '锁定技，每有一名道中存活，你的手牌上限便+1'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(thbrole.ChooseBossSkillAction)
class ChooseBossSkillAction:
    choose_option_prompt = '请选择BOSS技：'

    def choose_option_buttons(self, act):
        l = act.boss_skills
        return [(i.ui_meta.name, i.__name__) for i in l]

    def effect_string(self, act):
        return '|G【%s】|r选择了|G%s|r作为BOSS技' % (
            act.target.ui_meta.name,
            act.skill_chosen.ui_meta.name,
        )
