# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import actions
from thb.actions import PlayerTurn, ttags
from thb.cards import base, basic, definition as D
from thb.meta.common import N, ui_meta


# -- code --
@ui_meta(base.DummyCard)
class DummyCard:
    pass


@ui_meta(D.AttackCard)
class AttackCard:
    # action_stage meta
    name = '弹幕'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '出牌阶段，消耗1点干劲，对你攻击范围内的一名其他角色使用，对该角色造成1点伤害。'
        '<style=Desc.Li>默认情况下，你的攻击范围是1。</style>'
        '<style=Desc.Li>干劲在出牌阶段开始时恢复成1点。</style>'
    )

    def is_action_valid(self, c, tl):
        if not tl:
            return (False, '请选择弹幕的目标')

        return (True, '来一发！')

    def sound_effect(self, act):
        if not isinstance(act, actions.ActionStageLaunchCard):
            return 'thb-cv-card_attack1'

        g = self.game
        current = PlayerTurn.get_current(g).target

        if act.source is not current:
            return 'thb-cv-card_attack1'

        ttags(current)['__attack_graze_count'] += 1

        return [
            'thb-cv-card_attack1',
            'thb-cv-card_attack2',
            'thb-cv-card_attack3',
            'thb-cv-card_attack4',
        ][ttags(current)['__attack_graze_count'] % 4 - 1]


@ui_meta(D.GrazeCard)
class GrazeCard:
    # action_stage meta
    name = '擦弹'
    illustrator = '霏茶'
    cv = '小羽'
    description = (
        '当你受到<style=Card.Name>弹幕</style>的攻击时，你可以使用一张<style=Card.Name>擦弹</style>来抵消<style=Card.Name>弹幕</style>的效果。'
        '<style=Desc.Li>默认情况下，<style=Card.Name>擦弹</style>只能在回合外使用或打出。</style>'
    )

    def is_action_valid(self, c, tl):
        return False, '你不能主动使用擦弹'

    def effect_string(self, act):
        return f'{N.char(act.source)}使用了{N.card(act.card)}。'

    def sound_effect(self, act):
        if not isinstance(act, actions.LaunchCard):
            return 'thb-cv-card_graze1'

        g = self.game
        try:
            current = PlayerTurn.get_current(g).target
        except IndexError:
            return 'thb-cv-card_graze1'

        if act.source is not current:
            return 'thb-cv-card_graze1'

        cnt = ttags(current)['__attack_graze_count']
        if not cnt:
            return 'thb-cv-card_graze1'

        return [
            'thb-cv-card_graze1',
            'thb-cv-card_graze2',
            'thb-cv-card_graze3',
            'thb-cv-card_graze4',
        ][cnt % 4 - 1]


@ui_meta(D.WineCard)
class WineCard:
    # action_stage meta
    name = '酒'
    illustrator = '霏茶'
    cv = 'shourei小N'
    description = (
        '出牌阶段，对自己使用。使用后获得<style=B>喝醉</style>状态。'
        '<style=Desc.Li><style=B>喝醉</style>状态下，使用<style=Card.Name>弹幕</style>造成的伤害+1，受到致命伤害时伤害-1。</style>'
        '<style=Desc.Li>效果触发或者到了自己的准备阶段开始时须弃置<style=B>喝醉</style>状态。</style>'
        '<style=Desc.Li>你可以于喝醉状态下继续使用酒，但效果不叠加。</style>'
    )

    def is_action_valid(self, c, tl):
        me = self.me
        if me.tags.get('wine', False):
            return (True, '你已经醉了，还要再喝吗？')
        return (True, '嗝~~~ (*´ω`*)')

    def sound_effect(self, act):
        return 'thb-cv-card_wine'


@ui_meta(basic.Wine)
class Wine:
    def effect_string(self, act):
        return f'{N.char(act.target)}喝醉了…'


@ui_meta(basic.WineRevive)
class WineRevive:
    def effect_string(self, act):
        return f'{N.char(act.target)}醒酒了。'


@ui_meta(D.ExinwanCard)
class ExinwanCard:
    # action_stage meta
    name = '恶心丸'
    illustrator = '霏茶'
    cv = 'shourei小N'
    description = (
        '出牌阶段，对自己使用。使用时没有额外效果。当此牌以任意的方式进入弃牌堆时，引发弃牌动作的角色需选择其中一项执行：'
        '<style=Desc.Li>受到1点无来源伤害。</style>'
        '<style=Desc.Li>弃置两张牌。</style>'
        '<style=Desc.Attention>当你因为其他角色装备效果(如他人发动白楼剑特效）或技能效果（如正邪挑拨，秦心暗黑能乐）而将恶心丸主动置入弃牌堆时，恶心丸的弃置者视为该角色。</style>'
    )

    def is_action_valid(self, c, tl):
        return (True, '哼，哼，哼哼……')


@ui_meta(basic.ExinwanEffect)
class ExinwanEffect:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '节操给你，离我远点！')
        else:
            return (False, '请选择两张牌（不选则受到一点无源伤害）')

    def effect_string_before(self, act):
        return f'{N.char(act.target)}被恶心到了！'

    def sound_effect(self, act):
        return 'thb-cv-card_exinwan'


@ui_meta(basic.UseGraze)
class UseGraze:
    # choose_card meta

    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '我闪！')
        else:
            return (False, '请打出一张<style=Card.Name>擦弹</style>…')

    def effect_string(self, act):
        if not act.succeeded: return None
        t = act.target
        return f'{N.char(t)}打出了{N.card(act.card)}。'


@ui_meta(basic.LaunchGraze)
class LaunchGraze:
    # choose_card meta

    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '我闪！')
        else:
            return False, f'请使用一张{N.card(D.GrazeCard)}抵消{N.card(D.AttackCard)}效果…'


@ui_meta(basic.UseAttack)
class UseAttack:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '打架？来吧！')
        else:
            return (False, '请打出一张弹幕…')

    def effect_string(self, act):
        if not act.succeeded: return None
        t = act.target
        return f'{N.char(t)}打出了{N.card(act.card)}。'


@ui_meta(D.HealCard)
class HealCard:
    # action_stage meta
    name = '麻薯'
    illustrator = '霏茶'
    cv = 'VV'
    description = (
        '你可以在如下状况中使用，回复1点体力：\n'
        '<style=Desc.Li>在你的出牌阶段且你的当前体力小于最大体力。\n'
        '<style=Desc.Li>当有角色处于濒死状态时。'
    )

    def is_action_valid(self, c, tl):
        target = tl[0]

        if target.life >= target.maxlife:
            return (False, '您已经吃饱了')
        else:
            return (True, '来一口，精神焕发！')

    def sound_effect(self, act):
        return 'thb-cv-card_heal'


@ui_meta(basic.AskForHeal)
class AskForHeal:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return True, f'神说，你不能在这里被击坠(对{N.char(act.source)}使用)'
        else:
            return False, f'请选择一张<style=Card.Name>麻薯</style>对{N.char(act.source)}使用)…'


@ui_meta(basic.Heal)
class Heal:
    def effect_string(self, act):
        if act.succeeded:
            return f'{N.char(act.target)}回复了{act.amount}点体力。'
