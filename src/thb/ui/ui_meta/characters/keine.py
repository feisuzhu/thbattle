# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import gen_metafunc, my_turn, passive_clickable, passive_is_action_valid
from thb.actions import ttags


# -- code --
__metaclass__ = gen_metafunc(characters.keine)


class Devour:
    # Skill
    name = u'噬史'
    description = (
        u'每轮限一次。一名角色的出牌阶段开始时，你可以弃置一张基本牌，并根据其颜色发动相应效果：\n'
        u'|B|R>> |r若为红色，你记录该角色当前的体力值\n'
        u'|B|R>> |r若为黑色，你记录该角色当前的手牌数\n'
        u'该角色的出牌阶段结束时，将其恢复至本回合记录时的状态。'
    )
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DevourAction:
    pass


class DevourEffect:
    pass


class DevourHandler:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'发动「噬史」')
        else:
            return (False, u'请弃置一张牌基本牌发动「噬史」（否则不发动）')


class Teach:
    # Skill
    name = u'授业'
    description = (
        u'出牌阶段限一次，你可以重铸一张牌，然后将一张牌交给一名其它角色，其选择一项：|B|R>> |r使用一张牌，|B|R>> |r重铸一张牌。'
    )

    def clickable(g):
        return my_turn() and not ttags(g.me)['teach_used']

    def is_action_valid(g, cl, tl):
        cards = cl[0].associated_cards

        if not cards or len(cards) != 1:
            return False, u'请选择一张牌（重铸）'

        if not tl or len(tl) != 1:
            return False, u'请选择一个目标'

        return True, u'发动「授业」'

    def effect_string(act):
        return u'授业 effect_string'


class TeachAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'给出这张牌')
        else:
            return (False, u'请选择你要给出的牌')

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'传道授业！')


class TeachTargetEffect:
    # choose_option
    choose_option_buttons = ((u'重铸一张牌', 'reforge'), (u'使用卡牌', 'action'))
    choose_option_prompt = u'授业：请选择你的行动'


class TeachTargetReforgeAction:
    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'重铸这张牌')
        else:
            return (False, u'请选择一张牌重铸')

    def target(pl):
        if not pl:
            return (False, u'请选择1名玩家')

        return (True, u'传道授业！')


class KeineGuard:
    # Skill
    name = u'守护'
    description = (
        u'|B觉醒技|r，回合开始阶段，若你的体力值为全场最少或之一，你减少一点体力上限并获得技能|R噬史|r：\n'
        u'每轮限一次。一名角色的出牌阶段开始时，你可以弃置一张基本牌，并根据其颜色发动相应效果：\n'
        u'|B|R>> |r若为红色，你记录该角色当前的体力值\n'
        u'|B|R>> |r若为黑色，你记录该角色当前的手牌数\n'
        u'该角色的出牌阶段结束时，将其恢复至本回合记录时的状态。'
    )
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class KeineGuardAwake:
    def effect_string(act):
        return u'CAVED!!!!'


class Keine:
    # Character
    name        = u'上白泽慧音'
    title       = u'人间之里的守护者'
    designer    = u'沙包要不要'
    illustrator = u'和茶'
    # cv          = u'-'

    port_image        = u'thb-portrait-keine'
    figure_image      = u'thb-figure-keine'
    # miss_sound_effect = u'thb-cv-keine_miss'

'''
人间之里的守护者
4体力

噬史（每轮限一次，一名角色的出牌阶段开始时，你可以弃置一张基本牌。若为红，你记录该角色当前的体力值，若为黑，你记录该角色当前的手牌数。该角色的出牌阶段结束时，将其恢复至本回合记录时的状态）。
'''
