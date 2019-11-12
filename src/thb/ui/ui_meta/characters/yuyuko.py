# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable, passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.yuyuko)


class Yuyuko:
    # Character
    name        = '西行寺幽幽子'
    title       = '幽冥阁楼的吃货少女'
    illustrator = '和茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-yuyuko'
    figure_image      = 'thb-figure-yuyuko'
    miss_sound_effect = 'thb-cv-yuyuko_miss'

    notes = u'|RKOF不平衡角色'


class GuidedDeath:
    # Skill
    name = '诱死'
    description = '出牌阶段限一次，你可以令一名其它角色失去一点体力，然后其于回合结束阶段回复一点体力。回合结束阶段，若你于出牌阶段没有发动过该技能，则所有体力值为1的其它角色失去一点体力。'

    def clickable(g):
        me = g.me
        if ttags(me)['guided_death_active_use']:
            return False

        if not my_turn():
            return False

        return True

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        assert skill.is_card(characters.yuyuko.GuidedDeath)

        cards = skill.associated_cards

        if len(cards) != 0:
            return (False, '请不要选择牌')

        if not tl:
            return (False, '请选择『诱死』发动的目标')

        return (True, '发动「诱死」（回合结束时不再发动第二效果）')

    def effect_string(act):
        return '|G【%s】|r将|G【%s】|r献祭给了西行妖。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-yuyuko_pcb'


class SoulDrain:
    # Skill
    name = '离魂'
    description = (
        '你的回合内，当一名其他名角色进入濒死状态时，你摸一张牌，然后你可以与该角色拼点：\n'
        '|B|R>> |r若你赢，则将其体力上限改为1\n'
        '|B|R>> |r若你没赢，则将其体力值改为1'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class PerfectCherryBlossom:
    # Skill
    name = '反魂'
    description = (
        '|B锁定技|r，一名角色被击坠后，你增加一点体力上限并回复一点体力。你的手牌上限是你的体力上限。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class PerfectCherryBlossomExtractAction:

    def effect_string_before(act):
        return '幽雅地绽放吧，墨染的樱花！西行妖的力量又增强了一些。'

    def sound_effect_before(act):
        return 'thb-cv-yuyuko_pcb_extract'


class GuidedDeathEffect:
    def effect_string_apply(act):
        return '|G【%s】|r：“既然在座的各位中暑的中暑，受伤的受伤，不如都到花下沉眠吧！”' % (
            act.source.ui_meta.name,
        )


class SoulDrainEffect:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动『离魂』吗？'

    def effect_string_apply(act):
        return '|G【%s】|r微笑着站在一旁。|G【%s】|r似乎离死亡更近了一点。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect_before(act):
        return random.choice([
            'thb-cv-yuyuko_souldrain1',
            'thb-cv-yuyuko_souldrain2',
        ])
