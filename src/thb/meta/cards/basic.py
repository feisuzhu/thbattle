# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions
from thb.actions import ttags
from thb.cards import basic, definition
from thb.meta.common import G, ui_meta


# -- code --
@ui_meta(definition.AttackCard)
class AttackCard:
    # action_stage meta
    image = 'thb-card-attack'
    name = '弹幕'
    description = (
        '|R弹幕|r\n\n'
        '出牌阶段，消耗1点干劲，对你攻击范围内的一名其他角色使用，对该角色造成1点伤害。\n'
        '|B|R>> |r默认情况下，你的攻击范围是1。\n'
        '|B|R>> |r干劲在出牌阶段开始时恢复成1点。\n'
        '\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    def is_action_valid(self, g, cl, tl):
        if not tl:
            return (False, '请选择弹幕的目标')

        return (True, '来一发！')

    def sound_effect(self, act):
        if not isinstance(act, actions.ActionStageLaunchCard):
            return 'thb-cv-card_attack1'

        current = G().current_player

        if act.source is not current:
            return 'thb-cv-card_attack1'

        ttags(current)['__attack_graze_count'] += 1

        return [
            'thb-cv-card_attack1',
            'thb-cv-card_attack2',
            'thb-cv-card_attack3',
            'thb-cv-card_attack4',
        ][ttags(current)['__attack_graze_count'] % 4 - 1]


@ui_meta(definition.GrazeCard)
class GrazeCard:
    # action_stage meta
    name = '擦弹'
    image = 'thb-card-graze'
    description = (
        '|R擦弹|r\n\n'
        '当你受到|G弹幕|r的攻击时，你可以使用一张|G擦弹|r来抵消|G弹幕|r的效果。\n'
        '|B|R>> |r默认情况下，|G擦弹|r只能在回合外使用或打出。\n\n'
        '|DB（画师：霏茶，CV：小羽）|r'
    )

    def is_action_valid(self, g, cl, tl):
        return (False, '你不能主动使用擦弹')

    def effect_string(self, act):
        return '|G【%s】|r使用了|G%s|r。' % (
            act.source.ui_meta.name,
            act.card.ui_meta.name
        )

    def sound_effect(self, act):
        if not isinstance(act, actions.LaunchCard):
            return 'thb-cv-card_graze1'

        current = G().current_player

        if act.source is not current:
            return 'thb-cv-card_graze1'

        return [
            'thb-cv-card_graze1',
            'thb-cv-card_graze2',
            'thb-cv-card_graze3',
            'thb-cv-card_graze4',
        ][ttags(current)['__attack_graze_count'] % 4 - 1]


@ui_meta(definition.WineCard)
class WineCard:
    # action_stage meta
    name = '酒'
    image = 'thb-card-wine'
    description = (
        '|R酒|r\n\n'
        '出牌阶段，对自己使用。使用后获得|B喝醉|r状态。\n'
        '|B喝醉|r状态下，使用【弹幕】造成的伤害+1，受到致命伤害时伤害-1。\n'
        '|B|R>> |r 效果触发或者到了自己的准备阶段开始时须弃掉|B喝醉|r状态。\n'
        '|B|R>> |r 你可以于喝醉状态下继续使用酒，但效果不叠加。\n\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )

    def is_action_valid(self, g, cl, tl):
        if g.me.tags.get('wine', False):
            return (True, '你已经醉了，还要再喝吗？')
        return (True, '青岛啤酒，神主也爱喝！')

    def sound_effect(self, act):
        return 'thb-cv-card_wine'


@ui_meta(basic.Wine)
class Wine:
    def effect_string(self, act):
        return '|G【%s】|r喝醉了…' % act.target.ui_meta.name


@ui_meta(basic.WineRevive)
class WineRevive:
    def effect_string(self, act):
        return '|G【%s】|r醒酒了。' % act.target.ui_meta.name


@ui_meta(definition.ExinwanCard)
class ExinwanCard:
    # action_stage meta
    name = '恶心丸'
    image = 'thb-card-exinwan'
    description = (
        '|R恶心丸|r\n'
        '\n'
        '出牌阶段，对自己使用。使用时没有额外效果。当此牌以任意的方式进入弃牌堆时，引发弃牌动作的角色需选择其中一项执行：\n'
        '|B|R>> |r受到1点无来源伤害\n'
        '|B|R>> |r弃置两张牌\n'
        '\n'
        '|B|R! |r 当你因为其他角色装备效果(如他人发动白楼剑特效）或技能效果（如正邪挑拨，秦心暗黑能乐）而将恶心丸主动置入弃牌堆时，恶心丸的弃置者视为该角色。\n'
        '\n'
        '|DB（画师：霏茶，CV：shourei小N）|r'
    )

    def is_action_valid(self, g, cl, tl):
        return (True, '哼，哼，哼哼……')


@ui_meta(basic.ExinwanEffect)
class ExinwanEffect:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '节操给你，离我远点！')
        else:
            return (False, '请选择两张牌（不选则受到一点无源伤害）')

    def effect_string_before(self, act):
        return '|G【%s】|r被恶心到了！' % act.target.ui_meta.name

    def sound_effect(self, act):
        return 'thb-cv-card_exinwan'


@ui_meta(basic.UseGraze)
class UseGraze:
    # choose_card meta

    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '我闪！')
        else:
            return (False, '请打出一张【擦弹】…')

    def effect_string(self, act):
        if not act.succeeded: return None
        t = act.target
        return '|G【%s】|r打出了|G%s|r。' % (
            t.ui_meta.name,
            act.card.ui_meta.name,
        )


@ui_meta(basic.LaunchGraze)
class LaunchGraze:
    # choose_card meta

    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '我闪！')
        else:
            return (False, '请使用一张【擦弹】抵消【弹幕】效果…')


@ui_meta(basic.UseAttack)
class UseAttack:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '打架？来吧！')
        else:
            return (False, '请打出一张弹幕…')

    def effect_string(self, act):
        if not act.succeeded: return None
        t = act.target
        return '|G【%s】|r打出了|G%s|r。' % (
            t.ui_meta.name,
            act.card.ui_meta.name,
        )


@ui_meta(definition.HealCard)
class HealCard:
    # action_stage meta
    image = 'thb-card-heal'
    name = '麻薯'
    description = (
        '|R麻薯|r\n'
        '\n'
        '你可以在如下状况中使用，回复1点体力：\n'
        '|B|R>> |r在你的出牌阶段且你的当前体力小于最大体力\n'
        '|B|R>> |r当有角色处于濒死状态时\n'
        '\n'
        '|DB（画师：霏茶，CV：VV）|r'
    )

    def is_action_valid(self, g, cl, tl):
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
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '神说，你不能在这里被击坠(对%s使用)' % act.source.ui_meta.name)
        else:
            return (False, '请选择一张【麻薯】(对%s使用)…' % act.source.ui_meta.name)


@ui_meta(basic.Heal)
class Heal:
    def effect_string(self, act):
        if act.succeeded:
            return '|G【%s】|r回复了%d点体力。' % (
                act.target.ui_meta.name, act.amount
            )
