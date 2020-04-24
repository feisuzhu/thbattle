# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.koishi)


class Unconsciousness:
    name = u'无我'
    description = u'|B锁定技|r，你的回合内手牌数不小于体力的其他角色不能使用或打出牌，且你对其造成的伤害-1。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class UnconsciousnessAction:
    def effect_string(act):
        return u'|G【%s】|r：“……”' % (
            act.source.ui_meta.name,
        )


class UnconsciousnessLimit:
    target_independent = True
    shootdown_message = u'【无意识】你的手牌数不小于体力值，不能使用或打出任一张牌'


class Paranoia:
    name = u'偏执'
    description = u'你的回合内，每当你对一名角色造成伤害后，该伤害若是|G弹幕|r效果造成的，直到回合结束时其所有技能失效且你的干劲置为一；若该伤害恰为0点，你可以获得其一张手牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ParanoiaAction:
    def effect_string(act):
        return u'|G【%s】|r发动了|G偏执|r，获得|G【%s】|r的一张手牌。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return ''


class ParanoiaHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【偏执】吗？'


class Koishi:
    # Character
    name        = u'古明地恋'
    title       = u'紧闭的恋之瞳'
    illustrator = u'和茶'
    designer    = u'真炎的爆发'
    cv          = u'暂缺'

    port_image        = u'thb-portrait-koishi'
    figure_image      = u'thb-figure-koishi'
    miss_sound_effect = u''
