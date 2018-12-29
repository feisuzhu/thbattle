# -*- coding: utf-8 -*-


# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, my_turn, passive_clickable, passive_is_action_valid


# -- code --


@ui_meta(characters.remilia.SpearTheGungnir)
class SpearTheGungnir:
    # Skill
    name = '神枪'
    description = (
        '满足下列条件之一时，你可以令你的|G弹幕|r不能被响应：\n'
        '|B|R>> |r目标角色的体力值 大于 你的体力值。\n'
        '|B|R>> |r目标角色的手牌数 小于 你的手牌数。'
    )
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.remilia.SpearTheGungnirAction)
class SpearTheGungnirAction:
    def effect_string(self, act):
        return '|G【%s】|r举起右手，将|G弹幕|r汇聚成一把命运之矛，向|G【%s】|r掷去！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-remilia_stg'


@ui_meta(characters.remilia.SpearTheGungnirHandler)
class SpearTheGungnirHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【神枪】吗？'


@ui_meta(characters.remilia.VampireKiss)
class VampireKiss:
    # Skill
    name = '红魔之吻'
    description = '|B锁定技|r，你使用红色|G弹幕|r时无距离限制。当你使用红色|G弹幕|r对一名其他角色造成伤害后，你回复1点体力。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.remilia.VampireKissAction)
class VampireKissAction:
    def effect_string_before(self, act):
        return '|G【%s】|r:“B型血，赞！”' % (
            act.source.ui_meta.name
        )

    def sound_effect(self, act):
        return 'thb-cv-remilia_vampirekiss'


@ui_meta(characters.remilia.ScarletMistAttackLimit)
class ScarletMistAttackLimit:
    target_independent = False
    shootdown_message = '红雾：你只能对距离1的角色使用弹幕'


@ui_meta(characters.remilia.ScarletMistAction)
class ScarletMistAction:
    def effect_string(self, act):
        src = act.source
        tl = list(act.target_list)
        try:
            tl.remove(src)
        except Exception:
            pass

        return '|G【%s】|r释放出了|G红雾|r，威严爆表！%s流了鼻血！' % (
            src.ui_meta.name,
            '、'.join(['|G【%s】|r' % p.ui_meta.name for p in tl]),
        )

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-remilia_scarletmist1',
            'thb-cv-remilia_scarletmist2',
        ])


@ui_meta(characters.remilia.ScarletMistEndAction)
class ScarletMistEndAction:
    def effect_string(self, act):
        return '|G红雾|r结束了。'


@ui_meta(characters.remilia.ScarletMist)
class ScarletMist:
    name = '红雾'
    description = (
        '|BBOSS技|r，|B限定技|r，出牌阶段，你可以选择至多X名其他角色（X为存活道中数量），直到你的下个回合开始阶段，所有角色受到以下影响：\n'
        '|B|R>> |r你与被选择的角色使用|G弹幕|r时无视距离，且使用|G弹幕|r造成伤害后回复等量的体力。\n'
        '|B|R>> |r其他角色使用|G弹幕|r时只能指定距离为1的目标。'
    )

    def clickable(self, g):
        me = g.me
        return my_turn() and not me.tags['scarlet_mist_used']

    def is_action_valid(self, g, cl, tl):
        skill = cl[0]
        if skill.associated_cards:
            return (False, '红雾：请不要选择牌！')

        if not tl:
            return (False, '红雾：选择目标')

        return (True, '红雾：选择这些角色获得增益效果')


@ui_meta(characters.remilia.Remilia)
class Remilia:
    # Character
    name        = '蕾米莉亚'
    title       = '永远幼小的红月'
    illustrator = '小D@星の妄想乡'
    cv          = 'VV'

    port_image        = 'thb-portrait-remilia'
    figure_image      = 'thb-figure-remilia'
    miss_sound_effect = 'thb-cv-remilia_miss'
