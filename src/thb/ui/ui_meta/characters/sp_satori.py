# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import card_desc, gen_metafunc, my_turn, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.sp_satori)


class ThirdEye:
    # Skill
    name = u'3rd Eye'
    description = (
        u'每当你受到伤害后，你可以随机抽取三张角色牌，并声明其中一个非觉醒、非限定、非boss的技能，并获得技能“想起”，此技能效果等同于你声明的技能，如果你已经拥有“想起”的技能，则新技能会替换它（你只能拥有一个被“想起”的技能）。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class ThirdEyeChooseGirl:
    # char choice
    def effect_string(act):
        return u'|G【%s】|r选择了|G【%s】|r的技能组。' % (
            act.source.ui_meta.name,
            act.char_choice.ui_meta.name,
        )


class ThirdEyeAction:
    # choose_option meta
    choose_option_prompt = u'请选择【想起】的技能：'

    def choose_option_buttons(act):
        return [
            (s.ui_meta.name, n)
            for n, s in act.mapping.items()
        ]

    def effect_string_apply(act):
        return u'|G【%s】|r发动了|G3rd Eye|r，更新了技能|G【想起】|r。' % (
            act.source.ui_meta.name,
        ) if act.source.tags['recollected_char'] else \
            u'|G【%s】|r发动了|G3rd Eye|r，获得了技能|G【想起】|r。' % (
            act.source.ui_meta.name,
        )

    def effect_string(act):
        if getattr(act, 'sk_choice', None):
            act.sk_choice.ui_meta.name = '想起'

            return u'|G【%s】|r想起了技能|G【%s】|r。' % (
                act.source.ui_meta.name,
                act.sk_choice.ui_meta.name,
            )

    # tewi se to mock
    def sound_effect(act):
        return random.choice([
            'thb-cv-tewi_lucky',
            'thb-cv-tewi_miss',
        ])


class ThirdEyeHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【3rd Eye】吗？'


class Rosa:
    # Skill
    name = u'蔷薇'
    description = u'出牌阶段限一次，你可以重铸游戏中任意一张明牌区内的牌；当你对一名其他角色造成伤害时，你可以将其手牌中的一张牌置入明牌区。'

    def clickable(g):
        if g.me.tags['rosa_reforge'] >= g.me.tags['turn_count']:
            return False

        return my_turn() and any(getattr(p, 'showncards') for p in g.players)

    def is_action_valid(g, cl, tl):
        if cl[0].associated_cards:
            return (False, u'请不要选择牌！')

        if not len(tl):
            return (False, u'请选择一只角色~')

        # for more str to complete:
        return (True, u'蔷薇の地狱！！！')

    # mock with nitori se
    def sound_effect(act):
        return random.choice([
            'thb-cv-nitori_dismantle',
            'thb-cv-nitori_dismantle_other',
        ])


class RosaReforgeAction:
    def effect_string(act):
        return u'|G【%s】|r的|G薔薇|r生效，|G【%s】|r的%s消失了！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(act.card)
        )

    def ray(act):
        return [(act.source, act.target)]

    # mock with suika se
    def sound_effect(act):
        return 'thb-cv-suika_drunkendream'


class RosaRevealAction:
    def effect_string(act):
        return u'|G【%s】|r的|G心花|r生效：|G【%s】|r内心深处的%s被读出了！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
            card_desc(act.card)
        )

    def ray(act):
        return [(act.source, act.target)]

    # mock using momiji se
    def sound_effect(act):
        return 'thb-cv-momiji_disarm'


class RosaHandler:
    # choose_option
    choose_option_prompt = u'你要发动【心花】吗？'
    choose_option_buttons = ((u'发动', True), (u'不发动', False))


class MindReadAction:
    def effect_string(act):
        src = act.source
        tl = list(act.target_list)

        return u'|G【%s】|r发动了|G读心|r，%s的身份已经被获知了！' % (
            src.ui_meta.name,
            tl[0].ui_meta.name,
        )

    def ray(act):
        return [(act.source, act.target_list[0])]


class MindRead:
    # Skill
    name = u'读心'
    description = u'|BBOSS技|r，|B限定技|r，出牌阶段，选择一名角色，你可以获知其身份。'

    def clickable(g):
        me = g.me
        return my_turn() and not me.tags['mind_read_used']

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        if skill.associated_cards:
            return (False, u'读心：请不要选择牌！')

        if not tl:
            return (False, u'读心：选择目标')

        if len(tl) > 1:
            return (False, u'只可以选一只角色读心哦~')

        return (True, u'读心：选择一角色获知其身份')

    # mock using rumia se
    def sound_effect(act):
        return 'thb-cv-rumia_miss'


class SpSatori:
    # Character
    name        = u'SP古明地觉'
    title       = u'幻灵录专项SP订稿'
    illustrator = u'月见'
    cv          = u'暂缺'

    port_image        = u'thb-portrait-sp_satori'
    figure_image      = u'thb-figure-sp_satori'
    miss_sound_effect = u'thb-cv-tenshi_miss'
