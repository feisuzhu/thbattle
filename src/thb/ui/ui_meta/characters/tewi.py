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
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class LuckDrawCards:
    def effect_string(act):
        return u'|G【%s】|r觉得手上没有牌就输了，于是又摸了2张牌。' % (
            act.source.ui_meta.char_name,
        )

    def sound_effect(act):
        return 'thb-cv-tewi_lucky'


class Tewi:
    # Character
    char_name = u'因幡帝'
    port_image = 'thb-portrait-tewi'
    miss_sound_effect = 'thb-cv-tewi_miss'
    description = (
        u'|DB幸运的腹黑兔子 因幡帝 体力：4|r\n\n'
        u'|G幸运|r：|B锁定技|r，当你失去最后的手牌时，你摸两张牌。\n\n'
        u'|DB（画师：Pixiv UID 654238，CV：北斗夜）|r'
    )
