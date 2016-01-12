# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.mokou)


class Mokou:
    # Character
    char_name = u'藤原妹红'
    port_image = 'thb-portrait-mokou'
    figure_image = 'thb-figure-mokou'
    miss_sound_effect = 'thb-cv-mokou_miss'
    description = (
        u'|DBFFF团资深团员 藤原妹红 体力：4|r\n\n'
        u'|G浴火|r：结束阶段开始时，你可以失去1点体力，然后摸两张牌。\n\n'
        u'|G重生|r：准备阶段开始时，你可以弃置X张红色牌，然后回复1点体力。（X为你的当前体力值）\n\n'
        u'|DB（画师：六仔OwO，CV：小羽）|r'
    )


class Ashes:
    # Skill
    name = u'浴火'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AshesAction:
    def effect_string_before(act):
        return u'|G【%s】|r：“不~可~饶~恕~！”' % (
            act.target.ui_meta.char_name
        )

    def sound_effect(act):
        return 'thb-cv-mokou_ashes'


class AshesHandler:
    # choose_option meta
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【浴火】吗？'


class Reborn:
    # Skill
    name = u'重生'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class RebornAction:
    def effect_string(act):
        return u'|G【%s】|r使用了|G重生|r。' % (
            act.target.ui_meta.char_name
        )

    def sound_effect(act):
        return 'thb-cv-mokou_reborn'


class RebornHandler:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'弃置这些牌并回复1点体力')
        else:
            return (False, u'重生：选择%d张红色牌弃置并回复一点体力' % act.target.life)
