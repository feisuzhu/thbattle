# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.cards import Card
from thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.yuyuko)


class Yuyuko:
    # Character
    name        = u'西行寺幽幽子'
    title       = u'幽冥阁楼的吃货少女'
    illustrator = u'和茶'
    cv          = u'VV'

    port_image        = u'thb-portrait-yuyuko'
    figure_image      = u'thb-figure-yuyuko'
    # miss_sound_effect = u'thb-cv-youmu_miss'


class GuidedDeath:
    # Skill
    name = u'诱死'
    description = u'|B锁定技|r，你的回合结束阶段，所有体力值为1的其它角色失去一点体力。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class SoulDrain:
    # Skill
    name = u'离魂'
    description = (
        u'当一名角色进入濒死状态时，你摸1张牌，然后你可以与该角色拼点：\n'
        u'|B|R>> |r若你赢，则将该角色的体力上限改为1\n'
        u'|B|R>> |r若你没赢，则将其体力值改为1'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class PerfectCherryBlossom:
    # Skill
    name = u'反魂'
    description = u'出牌阶段限一次，你可以弃置一张黑色牌，令一名已受伤角色失去一点体力，然后其回复一点体力。若在该过程中该角色死亡，改为你回复一点体力。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid

    def clickable(g):
        me = g.me
        if ttags(me)['perfect_cherry_blossom']:
            return False

        if my_turn():
            return True

        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        assert skill.is_card(characters.yuyuko.PerfectCherryBlossom)

        cards = skill.associated_cards

        if not (len(cards) == 1 and cards[0].color == Card.BLACK):
            return (False, u'请选择一张黑色牌')

        if not tl:
            return (False, u'请选择『反魂』发动的目标')

        tgt = tl[0]
        if not tgt.life < tgt.maxlife:
            return (False, u'只能选择已受伤的角色')

        return (True, u'PerfectCherryBlossom')

    def effect_string(act):
        return u'PerfectCherryBlossomAction'


# class GuidedDeathLifeLost:
#     def effect_string_apply(act):
#         return u'GuidedDeathLifeLost'


class GuidedDeathEffect:
    def effect_string_apply(act):
        return u'GuidedDeathEffect'


class SoulDrainEffect:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动『离魂』吗？'

    def effect_string_apply(act):
        return u'SoulDrainEffect'
