# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import actions, cards
from gamepack.thb.actions import ttags
from gamepack.thb.ui.ui_meta.common import G, gen_metafunc

# -- code --
__metaclass__ = gen_metafunc(cards)


class AttackCard:
    # action_stage meta
    image = 'thb-card-attack'
    name = u'弹幕'
    description = (
        u'|R弹幕|r\n\n'
        u'出牌阶段，对你攻击范围内的一名其他角色使用，效果是对该角色造成1点伤害。\n'
        u'|B|R>> |r默认情况下，你的攻击范围是1。\n'
        u'|B|R>> |r默认情况下，出牌阶段你只能使用一张【弹幕】。\n\n'
        u'|DB（CV：VV）|r'
    )

    def is_action_valid(g, cl, target_list):
        if not target_list:
            return (False, u'请选择弹幕的目标')

        return (True, u'来一发！')

    def sound_effect(act):
        if not isinstance(act, actions.LaunchCard):
            return 'thb-cv-card_attack1'

        current = G().current_turn

        if act.source is not current:
            return 'thb-cv-card_attack1'

        ttags(current)['__attack_graze_count'] += 1

        return [
            'thb-cv-card_attack1',
            'thb-cv-card_attack2',
            'thb-cv-card_attack3',
            'thb-cv-card_attack4',
        ][ttags(current)['__attack_graze_count'] % 4 - 1]


class GrazeCard:
    # action_stage meta
    name = u'擦弹'
    image = 'thb-card-graze'
    description = (
        u'|R擦弹|r\n\n'
        u'当你受到【弹幕】的攻击时，你可以使用一张【擦弹】来抵消【弹幕】的效果。\n'
        u'|B|R>> |r默认情况下，【擦弹】只能在回合外使用或打出。\n\n'
        u'|DB（画师：霏茶，CV：小羽）|r'
    )

    def is_action_valid(g, cl, target_list):
        return (False, u'你不能主动使用擦弹')

    def effect_string(act):
        return u'|G【%s】|r使用了|G%s|r。' % (
            act.source.ui_meta.char_name,
            act.card.ui_meta.name
        )

    def sound_effect(act):
        if not isinstance(act, actions.LaunchCard):
            return 'thb-cv-card_graze1'

        current = G().current_turn

        if act.source is not current:
            return 'thb-cv-card_graze1'

        return [
            'thb-cv-card_graze1',
            'thb-cv-card_graze2',
            'thb-cv-card_graze3',
            'thb-cv-card_graze4',
        ][ttags(current)['__attack_graze_count'] % 4 - 1]


class WineCard:
    # action_stage meta
    name = u'酒'
    image = 'thb-card-wine'
    description = (
        u'|R酒|r\n\n'
        u'出牌阶段，对自己使用。使用后获得|B喝醉|r状态。\n'
        u'|B喝醉|r状态下，使用【弹幕】造成的伤害+1，受到致命伤害时伤害-1。\n'
        u'|B|R>> |r 效果触发或者到了自己的准备阶段开始时须弃掉|B喝醉|r状态。\n'
        u'|B|R>> |r 你可以于喝醉状态下继续使用酒，但效果不叠加。\n\n'
        u'|DB（CV：shourei小N）|r'
    )

    def is_action_valid(g, cl, target_list):
        if g.me.tags.get('wine', False):
            return (True, u'你已经醉了，还要再喝吗？')
        return (True, u'青岛啤酒，神主也爱喝！')

    def sound_effect(act):
        return 'thb-cv-card_wine'


class Wine:
    def effect_string(act):
        return u'|G【%s】|r喝醉了…' % act.target.ui_meta.char_name


class WineRevive:
    def effect_string(act):
        return u'|G【%s】|r醒酒了。' % act.target.ui_meta.char_name


class ExinwanCard:
    # action_stage meta
    name = u'恶心丸'
    image = 'thb-card-exinwan'
    description = (
        u'|R恶心丸|r\n\n'
        u'出牌阶段，对自己使用。使用时没有额外效果。当此牌以任意的方式进入弃牌堆时，引发弃牌动作的角色需选择其中一项执行：\n'
        u'1.受到1点无来源伤害\n'
        u'2.弃置两张牌\n'
        u'|B|R>> |r 当你因为其他角色装备效果(如他人发动白楼剑特效）或技能效果（如正邪挑拨，秦心暗黑能乐）而将恶心丸主动置入弃牌堆时，恶心丸的弃置者视为该角色。\n\n'
        u'|DB（画师：Pixiv ID 1203877，CV：shourei小N）|r'
    )

    def is_action_valid(g, cl, target_list):
        return (True, u'哼，哼，哼哼……')


class ExinwanEffect:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'节操给你，离我远点！')
        else:
            return (False, u'请选择两张牌（不选则受到一点无源伤害）')

    def effect_string_before(act):
        return u'|G【%s】|r被恶心到了！' % act.target.ui_meta.char_name

    def sound_effect(act):
        return 'thb-cv-card_exinwan'


class UseGraze:
    # choose_card meta

    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'我闪！')
        else:
            return (False, u'请打出一张【擦弹】…')

    def effect_string(act):
        if not act.succeeded: return None
        t = act.target
        return u'|G【%s】|r打出了|G%s|r。' % (
            t.ui_meta.char_name,
            act.card.ui_meta.name,
        )


class LaunchGraze:
    # choose_card meta

    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'我闪！')
        else:
            return (False, u'请使用一张【擦弹】抵消【弹幕】效果…')


class UseAttack:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'打架？来吧！')
        else:
            return (False, u'请打出一张弹幕…')

    def effect_string(act):
        if not act.succeeded: return None
        t = act.target
        return u'|G【%s】|r打出了|G%s|r。' % (
            t.ui_meta.char_name,
            act.card.ui_meta.name,
        )


class HealCard:
    # action_stage meta
    image = 'thb-card-heal'
    name = u'麻薯'
    description = (
        u'|R麻薯|r\n\n'
        u'【麻薯】能在两种情况下使用：\n'
        u'1、在你的出牌阶段，你可以使用它来回复你的1点体力。\n'
        u'2、当有角色处于濒死状态时，你可以对该角色使用【麻薯】，防止该角色的死亡。\n'
        u'|B|R>> |r出牌阶段，若你没有损失体力，你不可以对自己使用【麻薯】。\n\n'
        u'|DB（画师：http://seiga.nicovideo.jp/seiga/im3031795，CV：VV）|r'
    )

    def is_action_valid(g, cl, target_list):
        target = target_list[0]

        if target.life >= target.maxlife:
            return (False, u'您已经吃饱了')
        else:
            return (True, u'来一口，精神焕发！')

    def sound_effect(act):
        return 'thb-cv-card_heal'


class AskForHeal:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'神说，你不能在这里MISS(对%s使用)' % act.source.ui_meta.char_name)
        else:
            return (False, u'请选择一张【麻薯】(对%s使用)…' % act.source.ui_meta.char_name)


class Heal:
    def effect_string(act):
        if act.succeeded:
            return u'|G【%s】|r回复了%d点体力。' % (
                act.target.ui_meta.char_name, act.amount
            )
