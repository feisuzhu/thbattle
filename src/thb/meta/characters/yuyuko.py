# -*- coding: utf-8 -*-


# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.meta.common import ui_meta, my_turn, passive_clickable, passive_is_action_valid


# -- code --


@ui_meta(characters.yuyuko.Yuyuko)
class Yuyuko:
    # Character
    name        = '西行寺幽幽子'
    title       = '幽冥阁楼的吃货少女'
    illustrator = '和茶'
    cv          = 'VV'

    port_image        = 'thb-portrait-yuyuko'
    figure_image      = 'thb-figure-yuyuko'
    miss_sound_effect = 'thb-cv-yuyuko_miss'

    notes = '|RKOF不平衡角色'


@ui_meta(characters.yuyuko.GuidedDeath)
class GuidedDeath:
    # Skill
    name = '诱死'
    description = '|B锁定技|r，你的回合结束阶段，所有体力值为1的其它角色失去一点体力。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.yuyuko.SoulDrain)
class SoulDrain:
    # Skill
    name = '离魂'
    description = (
        '当一名其他名角色进入濒死状态时，你摸1张牌，然后你可以与该角色拼点：\n'
        '|B|R>> |r若你赢，则将该角色的体力上限改为1\n'
        '|B|R>> |r若你没赢，则将其体力值改为1'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.yuyuko.PerfectCherryBlossom)
class PerfectCherryBlossom:
    # Skill
    name = '反魂'
    description = (
        '出牌阶段限一次，令一名已受伤角色失去一点体力，然后其回复一点体力。'
        '若你以此法击坠一名角色，你增加一点体力上限并回复一点体力，然后失去此技能。'
    )

    def clickable(self, g):
        me = g.me
        if ttags(me)['perfect_cherry_blossom']:
            return False

        if my_turn():
            return True

        return False

    def is_action_valid(self, g, cl, tl):
        skill = cl[0]
        assert skill.is_card(characters.yuyuko.PerfectCherryBlossom)

        cards = skill.associated_cards

        if len(cards) != 0:
            return (False, '请不要选择牌')

        if not tl:
            return (False, '请选择『反魂』发动的目标')

        tgt = tl[0]
        if not tgt.life < tgt.maxlife:
            return (False, '只能选择已受伤的角色')

        return (True, 'Perfect Cherry Blossom !')

    def effect_string(self, act):
        return '|G【%s】|r将|G【%s】|r献祭给了西行妖。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-yuyuko_pcb'


@ui_meta(characters.yuyuko.PerfectCherryBlossomExtractAction)
class PerfectCherryBlossomExtractAction:

    def effect_string_before(self, act):
        return '幽雅地绽放吧，墨染的樱花！西行妖的力量又增强了一些。'

    def sound_effect_before(self, act):
        return 'thb-cv-yuyuko_pcb_extract'


@ui_meta(characters.yuyuko.GuidedDeathEffect)
class GuidedDeathEffect:
    def effect_string_apply(self, act):
        return '|G【%s】|r微微一笑，身后的西行妖显得更加迷人，让人觉得不如就这样沉眠于花下好了。' % (
            act.source.ui_meta.name,
        )


@ui_meta(characters.yuyuko.SoulDrainEffect)
class SoulDrainEffect:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动『离魂』吗？'

    def effect_string_apply(self, act):
        return '|G【%s】|r来了兴致，操纵起|G【%s】|r的生死。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect_before(self, act):
        return random.choice([
            'thb-cv-yuyuko_souldrain1',
            'thb-cv-yuyuko_souldrain2',
        ])
