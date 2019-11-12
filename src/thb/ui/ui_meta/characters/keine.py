# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.ui.ui_meta.common import card_desc, gen_metafunc, my_turn, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.keine)


class Teach:
    # Skill
    name = '授业'
    description = (
        '出牌阶段限一次，你可以重铸一张牌，然后将一张牌交给一名其它角色，其选择一项：'
        '|B|R>> |r使用一张牌，|B|R>> |r重铸一张牌。'
    )

    def clickable(g):
        return my_turn() and not ttags(g.me)['teach_used']

    def is_action_valid(g, cl, tl):
        cards = cl[0].associated_cards

        if not cards or len(cards) != 1:
            return False, '请选择一张牌（重铸）'

        if not tl or len(tl) != 1:
            return False, '请选择一个目标'

        return True, '发动「授业」'

    def effect_string(act):
        return '“是这样的|G【%s】|r”，|G【%s】|r说道，“两个1相加是不等于⑨的。即使是两个⑥也不行。不不，天才来算也不行。”' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(act):
        return random.choice([
            'thb-cv-keine_teach1',
            'thb-cv-keine_teach2',
        ])


class TeachAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, '给出这张牌')
        else:
            return (False, '请选择你要给出的牌')

    def target(pl):
        if not pl:
            return (False, '请选择1名玩家')

        return (True, '传道授业！')


class TeachTargetEffect:
    # choose_option
    choose_option_buttons = (('重铸一张牌', 'reforge'), ('使用卡牌', 'action'))
    choose_option_prompt = '授业：请选择你的行动'


class TeachTargetReforgeAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, '重铸这张牌')
        else:
            return (False, '请选择一张牌重铸')

    def target(pl):
        if not pl:
            return (False, '请选择1名玩家')

        return (True, '传道授业！')


class KeineGuard:
    # Skill
    name = u'守护'
    description = (
        '|B限定技|r，出牌阶段开始时，你可以失去一点体力上限，令一名其它已受伤角色回复一点体力。之后，若其体力仍然是全场最低的，则你与其获得技能|R决意|r。\n'
        '|B|R>> |b决意|r：当你受到伤害时，若同样拥有|R决意|r的另一名角色的体力值比你高，则伤害改为由该角色承受。同样拥有|R决意|r的另一名角色于你的回合内摸牌/回复体力时，你摸相同数量的牌/回复相同的体力。'
    )
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class KeineGuardAction:
    def effect_string_before(act):
        return '“我绝对不会让你们碰到|G【%s】|r 一根手指的！”|G【%s】|r冲着所有人喊道。' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect_before(act):
        return random.choice([
            'thb-cv-keine_guard_awake',
        ])


class KeineGuardHandler:

    def target(pl):
        if not pl:
            return (False, u'守护：请选择1名其他角色（或不发动）')

        p = pl[0]
        if p.life >= p.maxlife:
            return False, u'目标角色没有受伤'

        return True, u'我的CP由我来守护！'


class Devoted:
    # Skill
    name = u'决意'
    description = (
        '当你受到伤害时，若同样拥有|R决意|r的另一名角色的体力值比你高，则伤害改为由该角色承受。同样拥有|R决意|r的另一名角色于你的回合内摸牌/回复体力时，你摸相同数量的牌/回复相同的体力。'
    )
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DevotedHeal:
    def effect_string(act):
        return '守护治疗效果台词 |G【%s】|r |G【%s】|r' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class DevotedDrawCards:
    def effect_string(act):
        return '守护摸牌效果台词 |G【%s】|r, %s张' % (
            act.target.ui_meta.name,
            act.amount,
        )


class DevotedAction:
    def effect_string(act):
        return '守护的保护效果台词 |G【%s】|r |G【%s】|r' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


class Keine:
    # Character
    name        = '上白泽慧音'
    title       = '人间之里的守护者'
    designer    = '沙包要不要'
    illustrator = '和茶'
    cv          = '银子'

    port_image        = 'thb-portrait-keine'
    figure_image      = 'thb-figure-keine'
    miss_sound_effect = 'thb-cv-keine_miss'

    notes = u'|RKOF不平衡角色|r'
