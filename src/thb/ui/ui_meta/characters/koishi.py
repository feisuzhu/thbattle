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
    description = u'|B锁定技|r，你对有手牌的角色造成的伤害-1，对没有手牌的角色造成的伤害+1。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class UnconsciousnessAction:
    def effect_string(act):
        return u'|G【%s】|r：“……”' % (
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return ''


class Paranoia:
    name = u'偏执'
    description = u'每当你对一名角色造成伤害后，若该伤害恰为0点，你可以获得其一张手牌，该伤害若是|G弹幕|r效果造成的，且当前是你的回合，你额外+1干劲。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ParanoiaAction:
    def effect_string(act):

        return u'|G【%s】|r发动了|G偏执|r，获得|G【%s】|r的一张手牌。\n|G【%s】|r的干劲当前为%s。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            act.source.ui_meta.name,
            act.source.tags['vitality'],
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
    cv          = u'暂缺'

    port_image        = u'thb-portrait-koishi'
    figure_image      = u'thb-figure-koishi'
    miss_sound_effect = u''


# As for names for skills, reference:
# https://en.touhouwiki.net/wiki/Koishi_Komeiji#Spell_Cards
