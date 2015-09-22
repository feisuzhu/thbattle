# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import actions, characters
from gamepack.thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.kanako)


class Kanako:
    # Character
    char_name = u'八坂神奈子'
    port_image = 'thb-portrait-kanako'
    miss_sound_effect = 'thb-cv-kanako_miss'
    description = (
        u'|DB山丘与湖泊的化身 八坂神奈子 体力：4|r\n\n'
        u'|G神德|r：摸牌阶段开始时，你可以放弃摸牌并选择一名其他角色，改为令其摸两张牌，然后该角色需展示并交给你一张牌，若其交给你的牌为红桃，你摸一张牌。\n\n'
        u'|G信仰|r：|B限定技|r，出牌阶段，你可以令你攻击范围内的所有其他角色选择一项：令你摸一张牌；或弃置你一张牌，然后视为你对其使用了一张|G弹幕|r或|G弹幕战|r。\n\n'
        u'|DB（画师：Pixiv ID 6725408，CV：北斗夜/VV）|r'
    )


class KanakoFaith:
    # Skill
    name = u'信仰'

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
            act.source.ui_meta.char_name,
            u'、'.join([u'|G【%s】|r' % p.ui_meta.char_name for p in act.target_list]),
        )

    def sound_effect(act):
        return 'thb-cv-kanako_faith'


class KanakoFaithCheers:
    def effect_string_before(act):
        return u'|G【%s】|r献上了信仰！' % (
            act.source.ui_meta.char_name,
        )


class KanakoFaithCounteract:
    def effect_string_before(act):
        return u'|G【%s】|r决定要拆台！' % (
            act.source.ui_meta.char_name,
        )


class KanakoFaithCounteractPart1:
    def effect_string(act):
        return u'|G【%s】|r弃置了|G【%s】|r的%s' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
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
        return u'|G【%s】|r发动了|G神德|r，目标是|G【%s】|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-kanako_virtue'
