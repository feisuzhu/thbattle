# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import card_desc, ui_meta, passive_clickable
from thb.meta.common import passive_is_action_valid


# -- code --


@ui_meta(characters.kanako.Kanako)
class Kanako:
    # Character
    name        = '八坂神奈子'
    title       = '山丘与湖泊的化身'
    illustrator = '和茶'
    cv          = '北斗夜/VV'

    port_image        = 'thb-portrait-kanako'
    figure_image      = 'thb-figure-kanako'
    miss_sound_effect = 'thb-cv-kanako_miss'

    notes = '|RKOF模式不可用|r'


@ui_meta(characters.kanako.KanakoKOF)
class KanakoKOF:
    # Character
    name        = '八坂神奈子'
    title       = '山丘与湖泊的化身'
    illustrator = '和茶'
    cv          = '北斗夜/VV'

    port_image        = 'thb-portrait-kanako'
    figure_image      = 'thb-figure-kanako'
    miss_sound_effect = 'thb-cv-kanako_miss'

    notes = '|RKOF修正角色|r'


@ui_meta(characters.kanako.KanakoFaith)
class KanakoFaith:
    # Skill
    name = '信仰'
    description = (
        '|B限定技|r，出牌阶段，你可以令你攻击范围内的所有其他角色依次选择一项：\n'
        '|B|R>> |r令你摸一张牌\n'
        '|B|R>> |r弃置你一张牌，然后你视为对其使用了一张|G弹幕|r或|G弹幕战|r（按此法使用的弹幕不消耗干劲）。'
    )

    def clickable(self, game):
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

    def is_action_valid(self, g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if cl:
            return (False, '请不要选择牌')

        if not tl:
            return (False, '没有符合条件的角色')
        else:
            return (True, '发动【信仰】')

    def effect_string(self, act):
        return '|G【%s】|r打开神社大门，开始收集|G信仰|r！%s表示很感兴趣。' % (
            act.source.ui_meta.name,
            '、'.join(['|G【%s】|r' % p.ui_meta.name for p in act.target_list]),
        )

    def sound_effect(self, act):
        return 'thb-cv-kanako_faith'


@ui_meta(characters.kanako.KanakoFaithCheers)
class KanakoFaithCheers:
    def effect_string_before(self, act):
        return '|G【%s】|r献上了信仰！' % (
            act.source.ui_meta.name,
        )


@ui_meta(characters.kanako.KanakoFaithCounteract)
class KanakoFaithCounteract:
    def effect_string_before(self, act):
        return '|G【%s】|r决定要拆台！' % (
            act.source.ui_meta.name,
        )


@ui_meta(characters.kanako.KanakoFaithCounteractPart1)
class KanakoFaithCounteractPart1:
    def effect_string(self, act):
        return '|G【%s】|r弃置了|G【%s】|r的%s' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(act.card),
        )


@ui_meta(characters.kanako.KanakoFaithCounteractPart2)
class KanakoFaithCounteractPart2:
    # choose_option meta
    choose_option_buttons = (('弹幕战', 'duel'), ('弹幕', 'attack'))
    choose_option_prompt = '信仰：请选择希望的效果'


@ui_meta(characters.kanako.KanakoFaithEffect)
class KanakoFaithEffect:
    # choose_option meta
    choose_option_buttons = (('弃置对方的牌', 'drop'), ('对方摸牌', 'draw'))
    choose_option_prompt = '信仰：请选择希望的效果'


@ui_meta(characters.kanako.Virtue)
class Virtue:
    # Skill
    name = '神德'
    description = '摸牌阶段，你可以放弃摸牌，改为令一名其他角色摸两张牌，然后其须展示并交给你一张牌，若交给你的牌为红桃牌，你摸一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.kanako.VirtueHandler)
class VirtueHandler:
    def target(self, pl):
        if not pl:
            return (False, '神德：请选择1名玩家')

        return (True, '神德：放弃摸牌，选定的目标摸2张牌')


@ui_meta(characters.kanako.VirtueAction)
class VirtueAction:
    def choose_card_text(self, g, act, cards):
        prompt = '神德：交给对方一张牌'
        return act.cond(cards), prompt

    def effect_string_before(self, act):
        return '|G【%s】|r对|G【%s】|r发动了|G神德|r。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def effect_string(self, act):
        return '|G【%s】|r归还了%s。' % (
            act.target.ui_meta.name,
            card_desc(act.card),
        )

    def sound_effect(self, act):
        return 'thb-cv-kanako_virtue'


@ui_meta(characters.kanako.KanakoFaithKOF)
class KanakoFaithKOF:
    # Skill
    name = '信仰'
    description = (
        '|B锁定技|r，结束阶段开始时，若你满足以下条件之一，将你的手牌补至X张（X为你的当前体力值）\n'
        '|B|R>> |r你的体力值大于对方\n'
        '|B|R>> |r你曾于出牌阶段对对方造成过伤害'

    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.kanako.KanakoFaithKOFAction)
class KanakoFaithKOFAction:
    def effect_string_before(self, act):
        return '|G【%s】|r又收到的%s张香火钱，比博丽神社不知道高到哪里去了！' % (
            act.target.ui_meta.name,
            act.amount,
        )

    def sound_effect(self, act):
        return 'thb-cv-kanako_faith'
