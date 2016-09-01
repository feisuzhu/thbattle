# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.tewi)


class Luck:
    # Skill
    name = u'幸运'
    description = u'|B锁定技|r，每当你失去最后的手牌时，你摸两张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class LuckDrawCards:
    def effect_string(act):
        return u'|G【%s】|r觉得手上没有牌就输了，于是又摸了2张牌。' % (
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-tewi_lucky'


class Tewi:
    # Character
    name        = u'因幡帝'
    title       = u'幸运的腹黑兔子'
    illustrator = u'和茶'
    cv          = u'北斗夜'

    port_image        = u'thb-portrait-tewi'
    figure_image      = u'thb-figure-tewi'
    miss_sound_effect = u'thb-cv-tewi_miss'

    notes = u'|RKOF模式不可用|r'
