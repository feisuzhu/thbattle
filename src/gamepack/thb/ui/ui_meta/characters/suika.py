# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from gamepack.thb import actions, characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc, passive_clickable, passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.suika)


class HeavyDrinkerWine:
    name = u'酒'


class HeavyDrinker:
    # Skill
    name = u'酒豪'

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
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )


class DrunkenDream:
    # Skill
    name = u'醉梦'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DrunkenDreamDrawCards:

    def sound_effect(act):
        return 'thb-cv-suika_drunkendream'


class Suika:
    # Character
    char_name = u'伊吹萃香'
    port_image = 'thb-portrait-suika'
    miss_sound_effect = 'thb-cv-suika_miss'
    description = (
        u'|DB小小的酒鬼夜行 伊吹萃香 体力：4|r\n\n'
        u'|G酒豪|r：出牌阶段，你可以与一名角色拼点，若你赢，你和其各视为使用了一张【酒】，若你没赢，本回合你无法使用该技能。每阶段对每名角色限一次。\n\n'
        u'|G醉梦|r：|B锁定技|r，若你处于喝醉状态，你的攻击范围+2，回合开始阶段开始时，你摸1张牌。\n\n'
        u'|DB（画师：Pixiv ID 38236110，CV：shourei小N）|r'
    )
