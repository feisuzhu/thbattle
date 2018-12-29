# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid

# -- code --


@ui_meta(characters.tewi.Luck)
class Luck:
    # Skill
    name = '幸运'
    description = '|B锁定技|r，每当你失去最后的手牌时，你摸两张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.tewi.LuckDrawCards)
class LuckDrawCards:
    def effect_string(self, act):
        return '|G【%s】|r觉得手上没有牌就输了，于是又摸了2张牌。' % (
            act.source.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-tewi_lucky'


@ui_meta(characters.tewi.Tewi)
class Tewi:
    # Character
    name        = '因幡帝'
    title       = '幸运的腹黑兔子'
    illustrator = '和茶'
    cv          = '北斗夜'

    port_image        = 'thb-portrait-tewi'
    figure_image      = 'thb-figure-tewi'
    miss_sound_effect = 'thb-cv-tewi_miss'

    notes = '|RKOF模式不可用|r'
