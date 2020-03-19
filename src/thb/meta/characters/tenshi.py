# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import card_desc, ui_meta, passive_clickable
from thb.meta.common import passive_is_action_valid

# -- code --


@ui_meta(characters.tenshi.Masochist)
class Masochist:
    # Skill
    name = '抖Ｍ'
    description = '每当你受到1点伤害后，你可以观看牌堆顶的两张牌，并将这些牌交给至少一名角色。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.tenshi.MasochistHandler)
class MasochistHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【抖Ｍ】吗？'


@ui_meta(characters.tenshi.MasochistAction)
class MasochistAction:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '给你牌~')
        else:
            return (False, '请选择你要给出的牌（否则给自己）')

    def target(self, pl):
        if not pl:
            return (False, '请选择1名玩家')

        return (True, '给你牌~')

    def effect_string_before(self, act):
        return '不过|G【%s】|r好像很享受的样子…' % (
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-tenshi_masochist'


@ui_meta(characters.tenshi.ScarletPerception)
class ScarletPerception:
    # Skill
    name = '绯想'
    description = '|B锁定技|r，距离1以内的角色的红色判定牌生效后，你获得之。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.tenshi.ScarletPerceptionAction)
class ScarletPerceptionAction:
    def effect_string(act):
        return '|G【%s】|r获得了%s。' % (
            act.source.ui_meta.name,
            card_desc(act.card)
        )

    def sound_effect(self, act):
        return 'thb-cv-tenshi_sp'


@ui_meta(characters.tenshi.Tenshi)
class Tenshi:
    # Character
    name        = '比那名居天子'
    title       = '有顶天的大M子'
    illustrator = '月见'
    cv          = 'VV'

    port_image        = 'thb-portrait-tenshi'
    figure_image      = 'thb-figure-tenshi'
    miss_sound_effect = 'thb-cv-tenshi_miss'
