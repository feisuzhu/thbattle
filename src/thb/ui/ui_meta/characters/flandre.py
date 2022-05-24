# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.flandre)


class Flandre:
    # Character
    name        = u'芙兰朵露'
    title       = u'恶魔之妹'
    illustrator = u'月见'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-flandre'
    figure_image      = u'thb-figure-flandre'
    miss_sound_effect = u'thb-cv-flandre_miss'


class CriticalStrike:
    # Skill
    name = u'狂咲'
    description = (
        u'|B锁定技|r，你使用弹幕或弹幕战造成的伤害+1。你没有干劲时可以对出牌阶段内没有成为过弹幕目标的其他角色使用弹幕。回合结束时，如果你内造成过伤害，须弃置一张牌。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CriticalStrikeLimit:
    target_independent = False
    shootdown_message = u'你对这个角色使用过弹幕了'


class CriticalStrikeAction:
    def effect_string(act):
        return u'|G【%s】|r 狂咲效果' % (
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-flandre_cs'


class CriticalStrikeDropAction:
    def effect_string(act):
        return u'|G【%s】|r 狂咲弃牌效果' % (
            act.target.ui_meta.name,
        )

    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'「狂咲」：弃置这张牌')
        else:
            return (False, u'「狂咲」：请弃置一张牌')


class Exterminate:
    # Skill
    name = u'毁灭'
    description = u'|B锁定技|r，每当你使用|G弹幕|r或|G弹幕战|r指定其他角色为目标后，其所有技能无效直到回合结束。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ExterminateAction:
    def effect_string(act):
        return u'|G【%s】|r被|G【%s】|r玩坏了……' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return None
        return 'thb-cv-flandre_cs'
