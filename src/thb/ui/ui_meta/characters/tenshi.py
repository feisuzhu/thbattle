# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.tenshi)


class Masochist:
    # Skill
    name = u'抖Ｍ'
    description = u'当你受到1点伤害后，你可以观看牌堆顶的两张牌，将其中一张交给一名角色，然后将另一张交给一名角色。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class MasochistHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【抖Ｍ】吗？'


class MasochistAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'给你牌~')
        else:
            return (False, u'请选择你要给出的牌（否则给自己）')

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'给你牌~')

    def effect_string_before(act):
        return u'不过|G【%s】|r好像很享受的样子…' % (
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-tenshi_masochist'


class ScarletPerception:
    # Skill
    name = u'绯想'
    description = u'|B锁定技|r，与你距离为1以内的角色的红色判定牌进入弃牌堆后，你获得之。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ScarletPerceptionAction:
    def effect_string(act):
        return u'|G【%s】|r获得了%s' % (
            act.source.ui_meta.name,
            card_desc(act.card)
        )

    def sound_effect(act):
        return 'thb-cv-tenshi_sp'


class Tenshi:
    # Character
    name        = u'比那名居天子'
    title       = u'有顶天的大M子'
    illustrator = u'月见'
    cv          = u'VV'

    port_image        = u'thb-portrait-tenshi'
    figure_image      = u'thb-figure-tenshi'
    miss_sound_effect = u'thb-cv-tenshi_miss'
