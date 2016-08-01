# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.kanako)


class Kanako:
    # Character
    name        = u'八坂神奈子'
    title       = u'山丘与湖泊的化身'
    illustrator = u'和茶'
    cv          = u'北斗夜/VV'

    port_image        = u'thb-portrait-kanako'
    figure_image      = u'thb-figure-kanako'
    miss_sound_effect = u'thb-cv-kanako_miss'

    notes = u'|RKOF模式不可用|r'


class KanakoKOF:
    # Character
    name        = u'八坂神奈子'
    title       = u'山丘与湖泊的化身'
    illustrator = u'和茶'
    cv          = u'北斗夜/VV'

    port_image        = u'thb-portrait-kanako'
    figure_image      = u'thb-figure-kanako'
    miss_sound_effect = u'thb-cv-kanako_miss'

    notes = u'|RKOF修正角色|r'


class KanakoFaith:
    # Skill
    name = u'信仰'
    description = (
        u'|B限定技|r，出牌阶段，你可以令你攻击范围内的所有其他角色依次选择一项：\n'
        u'|B|R>> |r令你摸一张牌\n'
        u'|B|R>> |r弃置你一张牌，然后你视为对其使用了一张|G弹幕|r或|G弹幕战|r（按此法使用的弹幕不消耗干劲）。'
    )

    def clickable(game):
        me = game.me
        if me.tags['kanako_faith']:
            return False

        try:
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True

        except IndexError:
            pass

        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if cl:
            return (False, u'请不要选择牌')

        if not tl:
            return (False, u'没有符合条件的角色')
        else:
            return (True, u'发动【信仰】')

    def effect_string(act):
        return u'|G【%s】|r打开神社大门，开始收集|G信仰|r！%s表示很感兴趣。' % (
            act.source.ui_meta.name,
            u'、'.join([u'|G【%s】|r' % p.ui_meta.name for p in act.target_list]),
        )

    def sound_effect(act):
        return 'thb-cv-kanako_faith'


class KanakoFaithCheers:
    def effect_string_before(act):
        return u'|G【%s】|r献上了信仰！' % (
            act.source.ui_meta.name,
        )


class KanakoFaithCounteract:
    def effect_string_before(act):
        return u'|G【%s】|r决定要拆台！' % (
            act.source.ui_meta.name,
        )


class KanakoFaithCounteractPart1:
    def effect_string(act):
        return u'|G【%s】|r弃置了|G【%s】|r的%s' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(act.card),
        )


class KanakoFaithCounteractPart2:
    # choose_option meta
    choose_option_buttons = ((u'弹幕战', 'duel'), (u'弹幕', 'attack'))
    choose_option_prompt = u'信仰：请选择希望的效果'


class KanakoFaithEffect:
    # choose_option meta
    choose_option_buttons = ((u'弃置对方的牌', 'drop'), (u'对方摸牌', 'draw'))
    choose_option_prompt = u'信仰：请选择希望的效果'


class Virtue:
    # Skill
    name = u'神德'
    description = u'摸牌阶段，你可以放弃摸牌，改为令一名其他角色摸两张牌，然后其须展示并交给你一张牌，若交给你的牌为红桃牌，你摸一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class VirtueHandler:
    def target(pl):
        if not pl:
            return (False, u'神德：请选择1名玩家')

        return (True, u'神德：放弃摸牌，选定的目标摸2张牌')


class VirtueAction:
    def choose_card_text(g, act, cards):
        prompt = u'神德：交给对方一张牌'
        return act.cond(cards), prompt

    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r发动了|G神德|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def effect_string(act):
        return u'|G【%s】|r归还了%s。' % (
            act.target.ui_meta.name,
            card_desc(act.card),
        )

    def sound_effect(act):
        return 'thb-cv-kanako_virtue'


class KanakoFaithKOF:
    # Skill
    name = u'信仰'
    description = (
        u'|B锁定技|r，结束阶段开始时，若你满足以下条件之一，将你的手牌补至X张（X为你的当前体力值）\n'
        u'|B|R>> |r你的体力值大于对方\n'
        u'|B|R>> |r你曾于出牌阶段对对方造成过伤害'

    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class KanakoFaithKOFAction:
    def effect_string_before(act):
        return u'|G【%s】|r又收到的%s张香火钱，比博丽神社不知道高到哪里去了！' % (
            act.target.ui_meta.name,
            act.amount,
        )

    def sound_effect(act):
        return 'thb-cv-kanako_faith'
