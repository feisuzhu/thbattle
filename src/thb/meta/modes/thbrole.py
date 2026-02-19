# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import thbrole
from thb.actions import ttags
from thb.cards.classes import AttackCard
from thb.meta.common import ui_meta, UIMetaBare, N


# -- code --
@ui_meta(thbrole.THBattleRole)
class THBattleRole(UIMetaBare):
    name = '8人身份场'
    description = (
        '<style=B>身份分配</style>：1<sprite=Role.Boss>、2<sprite=Role.Accomplice>、1<sprite=Role.Curtain>、4<sprite=Role.Attacker>。'
        '<style=Desc.Li><sprite=Role.Boss>：<sprite=Role.Boss>的体力上限+1。游戏开局时展示身份，并获得BOSS技。胜利条件为击坠所有<sprite=Role.Attacker>以及<sprite=Role.Curtain>。</style>'
        '<style=Desc.Li><sprite=Role.Accomplice>：胜利条件为击坠所有<sprite=Role.Attacker>以及<sprite=Role.Curtain>。当<sprite=Role.Accomplice>被<sprite=Role.Boss>击坠后，<sprite=Role.Boss>需弃置所有手牌和装备牌。</style>'
        '<style=Desc.Li><sprite=Role.Attacker>：胜利条件为击坠<sprite=Role.Boss>。当<sprite=Role.Attacker>被击坠后，击坠者摸3张牌。</style>'
        '<style=Desc.Li><sprite=Role.Curtain>：胜利条件为在<sprite=Role.Attacker>全部被击坠的状况下击坠<sprite=Role.Boss>。</style>'
        # '<style=Desc.Li><style=B>双黑幕模式</style>：胜利条件条件是除了<sprite=Role.Boss>的其他人全部被击坠的情况下击坠<sprite=Role.Boss>。当<sprite=Role.Boss>被击坠时，若场上只有一名未被击坠的角色且其身份为<sprite=Role.Curtain>，则该<sprite=Role.Curtain>胜利，另一<sprite=Role.Curtain>失败；反之，两位<sprite=Role.Curtain>失败，而<sprite=Role.Attacker>阵营胜利。</style>'
        '\n'
        '玩家的身份会在被击坠后公开。<sprite=Role.Boss>的身份会在开局的时候公开。'
        '\n'
        '<style=B>BOSS技</style>：<sprite=Role.Boss>身份的玩家在开场会获得BOSS技。某些角色在在设定上有专属的BOSS技，开局时会额外获得。没有专属BOSS技的角色会在如下几个通用BOSS技中选择一个获得：'
        '<style=Desc.Li><style=Skill.Name>同仇</style>：当你需要使用或打出一张<style=Card.Name>弹幕</style>时，其他玩家可以代替你使用或打出一张<style=Card.Name>弹幕</style>。</style>'
        '<style=Desc.Li><style=Skill.Name>协力</style>：当你需要使用或打出一张<style=Card.Name>擦弹</style>时，其他玩家可以代替你使用或打出一张<style=Card.Name>擦弹</style>。</style>'
        '<style=Desc.Li><style=Skill.Name>牺牲</style>：当你于濒死状态下，被一名角色使用<style=Card.Name>麻薯</style>而回复体力至1后，其可以流失一点体力，令你额外回复一点体力。</style>'
        '<style=Desc.Li><style=Skill.Name>应援</style>：<style=B>锁定技</style>，每有一名道中存活，你的手牌上限增加一。</style>'
    ).strip()

    params = {
        'double_curtain': [
            ('正常模式', False),
            ('双黑幕模式', True),
        ],
    }

    roles = {
        'HIDDEN':     {'name': '？',   'sprite': 'role-hidden'},
        'BOSS':       {'name': 'BOSS', 'sprite': 'role-boss'},
        'ACCOMPLICE': {'name': '道中', 'sprite': 'role-accomplice'},
        'ATTACKER':   {'name': '城管', 'sprite': 'role-attacker'},
        'CURTAIN':    {'name': '黑幕', 'sprite': 'role-curtain'},
    }


@ui_meta(thbrole.AssistedAttack)
class AssistedAttack:
    # Skill
    name = '同仇'
    description = '当你需要使用或打出一张<style=Card.Name>弹幕</style>时，其他玩家可以代替你使用或打出一张<style=Card.Name>弹幕</style>。'

    def clickable(self):
        if not self.my_turn():
            return False

        if ttags(self.me)['assisted_attack_disable']:
            return False

        return True

    def is_action_valid(self, sk, tl):
        cl = sk.associated_cards
        if len(cl):
            return (False, '请不要选择牌！')

        return AttackCard().ui_meta.is_action_valid(sk, tl)

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return f'{N.char(act.source)}发动了<style=Skill.Name>同仇</style>，目标是{N.char(act.target)}。'


@ui_meta(thbrole.AssistedUseAction)
class AssistedUseAction:
    def choose_option_prompt(self, act):
        return f'你要帮BOSS出{N.card(act.their_afc_action.card_cls)}吗？'

    choose_option_buttons = (('帮BOSS', True), ('不关我事', False))


@ui_meta(thbrole.AssistedAttackAction)
class AssistedAttackAction:
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, f'帮BOSS对{N.char(act.target)}出弹幕')
        else:
            return (False, '<style=Skill.Name>同仇</style>：请选择一张弹幕（对{N.char(act.target)}出）')


@ui_meta(thbrole.AssistedAttackHandler)
class AssistedAttackHandler:
    choose_option_prompt = '你要发动<style=Skill.Name>同仇</style>吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(thbrole.AssistedGraze)
class AssistedGraze:
    # Skill
    name = '协力'
    description = '当你需要使用或打出一张<style=Card.Name>擦弹</style>时，其他玩家可以代替你使用或打出一张<style=Card.Name>擦弹</style>。'


@ui_meta(thbrole.AssistedGrazeHandler)
class AssistedGrazeHandler:
    choose_option_prompt = '你要发动<style=Skill.Name>协力</style>吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(thbrole.AssistedHealAction)
class AssistedHealAction:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}发动了<style=Skill.Name>牺牲</style>。'


@ui_meta(thbrole.AssistedHealHandler)
class AssistedHealHandler:
    choose_option_prompt = '你要发动<style=Skill.Name>牺牲</style>吗？'
    choose_option_buttons = (('发动', True), ('不发动', False))


@ui_meta(thbrole.AssistedHeal)
class AssistedHeal:
    # Skill
    name = '牺牲'
    description = '当你于濒死状态下，被一名角色使用<style=Card.Name>麻薯</style>而回复体力至1后，其可以流失一点体力，令你额外回复一点体力。'


@ui_meta(thbrole.ExtraCardSlot)
class ExtraCardSlot:
    # Skill
    name = '应援'
    description = '锁定技，每有一名道中存活，你的手牌上限增加一。'


@ui_meta(thbrole.ChooseBossSkillAction)
class ChooseBossSkillAction:
    choose_option_prompt = '请选择BOSS技：'

    def choose_option_buttons(self, act):
        l = act.boss_skills
        return [(i.ui_meta.name, i.__name__) for i in l]

    def effect_string(self, act):
        return f'{N.char(act.target)}选择了{N.card(act.skill_chosen)}作为BOSS技。'
