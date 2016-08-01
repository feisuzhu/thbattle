# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.suika)


class HeavyDrinkerWine:
    name = u'酒'


class HeavyDrinker:
    # Skill
    name = u'酒豪'
    description = u'出牌阶段每名角色限一次，你可以和其他角色拼点，若你赢，视为你和其各使用了一张|G酒|r，若你没赢，你不能发动此技能，直到回合结束。'

    def clickable(game):
        me = game.me

        if me.tags['suika_failed'] >= me.tags['turn_count']:
            return False

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if not isinstance(act, actions.ActionStage):
            return False

        return True

    def is_action_valid(g, cl, target_list):
        if cl[0].associated_cards:
            return False, u'请不要选择牌！'

        if not target_list:
            return False, u'请选择一名角色！'

        return True, u'来一杯！'

    def sound_effect(act):
        return 'thb-cv-suika_heavydrinker'

    def effect_string(act):
        return u'|G【%s】|r跟|G【%s】|r划起了拳：“哥俩好，三星照，只喝酒，不吃药！”' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class DrunkenDream:
    # Skill
    name = u'醉梦'
    description = u'|B锁定技|r，你处于“喝醉”状态时，攻击范围+2；准备阶段开始时，你摸一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DrunkenDreamDrawCards:

    def sound_effect(act):
        return 'thb-cv-suika_drunkendream'


class Suika:
    # Character
    name        = u'伊吹萃香'
    title       = u'小小的酒鬼夜行'
    illustrator = u'和茶'
    cv          = u'shourei小N'

    port_image        = u'thb-portrait-suika'
    figure_image      = u'thb-figure-suika'
    miss_sound_effect = u'thb-cv-suika_miss'
