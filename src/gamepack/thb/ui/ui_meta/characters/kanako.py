# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.kanako)


class Kanako:
    # Character
    char_name = u'八坂神奈子'
    port_image = 'thb-portrait-kanako'
    miss_sound_effect = 'thb-cv-kanako_miss'
    description = (
        u'|DB山丘与湖泊的化身 八坂神奈子 体力：4|r\n\n'
        u'|G神威|r：|B锁定技|r，摸牌阶段开始时，你摸X张牌，然后弃置等量的牌（X为你的当前体力值，且至多为4）。\n\n'
        u'|G神德|r：每名角色的回合限一次，你在自己的摸牌阶段以外获得牌时，你可以弃置一张手牌并令一名其他角色摸一张牌。\n\n'
        u'|DB（画师：Pixiv ID 6725408，CV：北斗夜/VV）|r'
    )


class Divinity:
    # Skill
    name = u'神威'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


# class DivinityHandler:
#     # choose_option meta
#     choose_option_buttons = ((u'发动', True), (u'不发动', False))
#     choose_option_prompt = u'你要发动【神威】吗？'

class DivinityDrawCards:
    def effect_string(act):
        return u'|G【%s】|r发动了|G神威|r，摸了%d张牌。' % (
            act.target.ui_meta.char_name, act.amount,
        )

    def sound_effect(act):
        return 'thb-cv-kanako_divinity'


class DivinityDropCards:
    def effect_string(act):
        return u'|G【%s】|r弃置了%d张牌。' % (
            act.target.ui_meta.char_name,
            len(act.cards),
        )


class DivinityAction:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'神威：弃置这些牌')
        else:
            return (False, u'神威：请弃置%d张牌' % act.amount)


class Virtue:
    # Skill
    name = u'神德'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class VirtueHandler:
    def choose_card_text(g, act, cards):
        prompt = u'神德：弃置1张牌，并选择一名其他角色（否则不发动）'
        return act.cond(cards), prompt

    def target(pl):
        if not pl:
            return (False, u'神德：请选择1名玩家')

        return (True, u'神德：选定的目标摸1张牌')


class VirtueAction:
    def effect_string_before(act):
        return u'|G【%s】|r发动了|G神德|r，目标是|G【%s】|r。' % (
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-kanako_virtue'
