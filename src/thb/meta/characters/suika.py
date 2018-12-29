# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid

# -- code --


@ui_meta(characters.suika.HeavyDrinkerWine)
class HeavyDrinkerWine:
    name = '酒'


@ui_meta(characters.suika.HeavyDrinker)
class HeavyDrinker:
    # Skill
    name = '酒豪'
    description = '出牌阶段每名角色限一次，你可以和其他角色拼点，若你赢，视为你和其各使用了一张|G酒|r，若你没赢，你不能发动此技能，直到回合结束。'

    def clickable(self, game):
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

    def is_action_valid(self, g, cl, target_list):
        if cl[0].associated_cards:
            return False, '请不要选择牌！'

        if not target_list:
            return False, '请选择一名角色！'

        return True, '来一杯！'

    def sound_effect(self, act):
        return 'thb-cv-suika_heavydrinker'

    def effect_string(self, act):
        return '|G【%s】|r跟|G【%s】|r划起了拳：“哥俩好，三星照，只喝酒，不吃药！”' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


@ui_meta(characters.suika.DrunkenDream)
class DrunkenDream:
    # Skill
    name = '醉梦'
    description = '|B锁定技|r，你处于“喝醉”状态时，攻击范围+2；准备阶段开始时，你摸一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.suika.DrunkenDreamDrawCards)
class DrunkenDreamDrawCards:

    def sound_effect(self, act):
        return 'thb-cv-suika_drunkendream'


@ui_meta(characters.suika.Suika)
class Suika:
    # Character
    name        = '伊吹萃香'
    title       = '小小的酒鬼夜行'
    illustrator = '和茶'
    cv          = 'shourei小N'

    port_image        = 'thb-portrait-suika'
    figure_image      = 'thb-figure-suika'
    miss_sound_effect = 'thb-cv-suika_miss'
