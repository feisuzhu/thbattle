# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import cards as thbcards, characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable
from gamepack.thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.shizuha)


class DecayAction:
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return True, u'弃置这些牌'

        else:
            return False, u'请选择一张基本牌或两张牌'


class Decay:
    # Skill
    name = u'凋零'

    def clickable(g):
        return my_turn()

    def is_action_valid(g, cl, tl):
        cl = cl[0].associated_cards

        if len(cl) != 2:
            return False, u'请选择两张黑色牌！'

        if any(c.color != thbcards.Card.BLACK for c in cl):
            return False, u'请选择两张黑色牌！'

        if len(tl) != 1:
            return False, u'请选择一名角色'

        return True, u'凋零！'


class AutumnLeaves:
    # Skill
    name = u'红叶'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AutumnLeavesHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))

    choose_option_prompt = u'你要发动【红叶】吗？'


class Shizuha:
    # Character
    char_name = u'秋静叶'
    port_image = 'thb-portrait-shizuha'
    description = (
        u'|DB寂寞与终焉的象征 秋静叶 体力：3|r\n\n'
        u'|G红叶|r：当其他角色的红色基本牌因使用或打出以外的原因进入弃牌堆后，你可以摸一张牌。\n\n'
        u'|G凋零|r：出牌阶段，你可以弃置两张黑色牌，然后令你攻击范围内一名其他角色选择一项：弃置一张基本牌，或弃置两张牌。若其以此法失去最后一张手牌后，对其造成一点伤害。'
    )
