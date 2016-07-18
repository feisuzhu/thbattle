# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.mokou)


class Mokou:
    # Character
    name        = u'藤原妹红'
    title       = u'FFF团资深团员'
    illustrator = u'六仔OwO'
    cv          = u'小羽'

    port_image        = u'thb-portrait-mokou'
    figure_image      = u'thb-figure-mokou'
    miss_sound_effect = u'thb-cv-mokou_miss'


class Ashes:
    # Skill
    name = u'浴火'
    description = u'结束阶段开始时，你可以失去1点体力，然后摸两张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class AshesAction:
    def effect_string_before(act):
        return u'|G【%s】|r：“不~可~饶~恕~！”' % (
            act.target.ui_meta.name
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
    description = u'准备阶段开始时，你可以弃置X张红色牌，然后回复1点体力。（X为你的当前体力值）'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class RebornAction:
    def effect_string(act):
        return u'|G【%s】|r使用了|G重生|r。' % (
            act.target.ui_meta.name
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
