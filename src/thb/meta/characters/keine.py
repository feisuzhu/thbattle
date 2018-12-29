# -*- coding: utf-8 -*-


# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.actions import ttags
from thb.meta.common import card_desc, ui_meta, my_turn, passive_clickable
from thb.meta.common import passive_is_action_valid


# -- code --


@ui_meta(characters.keine.Devour)
class Devour:
    # Skill
    name = '噬史'
    description = (
        '一名角色的出牌阶段开始时，你可以弃置一张基本牌或装备牌，并根据其颜色发动相应效果：\n'
        '|B|R>> |r若为红色，你记录该角色当前的体力值\n'
        '|B|R>> |r若为黑色，你记录该角色当前的手牌数\n'
        '该角色的出牌阶段结束时，将其恢复至本回合记录时的状态。'
    )
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.keine.DevourAction)
class DevourAction:
    def effect_string_before(self, act):
        return '|G【%s】|r默默地拿出了一张%s，把|G【%s】|r的%s记在了卡牌背面。' % (
            act.source.ui_meta.name,
            card_desc(act.card),
            act.target.ui_meta.name,
            '体力值' if act.effect == 'life' else '卡牌数'
        )

    def sound_effect_before(self, act):
        if act.effect == 'life':
            return 'thb-cv-keine_devour1'
        else:
            return 'thb-cv-keine_devour2'

        # return random.choice([
        #     'thb-cv-keine_devour1',
        #     'thb-cv-keine_devour2',
        #     'thb-cv-keine_devour3',
        # ])


@ui_meta(characters.keine.DevourEffect)
class DevourEffect:
    def effect_string_before(self, act):
        return '|G【%s】|r吞噬掉了刚才发生在|G【%s】|r身上的历史。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )


@ui_meta(characters.keine.DevourHandler)
class DevourHandler:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '发动「噬史」')
        else:
            return (False, '请弃置一张牌基本牌或装备牌发动「噬史」（否则不发动）')


@ui_meta(characters.keine.Teach)
class Teach:
    # Skill
    name = '授业'
    description = (
        '出牌阶段限一次，你可以重铸一张牌，然后将一张牌交给一名其它角色，其选择一项：'
        '|B|R>> |r使用一张牌，|B|R>> |r重铸一张牌。'
    )

    def clickable(self, g):
        return my_turn() and not ttags(g.me)['teach_used']

    def is_action_valid(self, g, cl, tl):
        cards = cl[0].associated_cards

        if not cards or len(cards) != 1:
            return False, '请选择一张牌（重铸）'

        if not tl or len(tl) != 1:
            return False, '请选择一个目标'

        return True, '发动「授业」'

    def effect_string(self, act):
        return '“是这样的|G【%s】|r”，|G【%s】|r说道，“两个1相加是不等于⑨的。即使是两个⑥也不行。不不，天才来算也不行。”' % (
            act.target.ui_meta.name,
            act.source.ui_meta.name,
        )

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-keine_teach1',
            'thb-cv-keine_teach2',
        ])


@ui_meta(characters.keine.TeachAction)
class TeachAction:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '给出这张牌')
        else:
            return (False, '请选择你要给出的牌')

    def target(self, pl):
        if not pl:
            return (False, '请选择1名玩家')

        return (True, '传道授业！')


@ui_meta(characters.keine.TeachTargetEffect)
class TeachTargetEffect:
    # choose_option
    choose_option_buttons = (('重铸一张牌', 'reforge'), ('使用卡牌', 'action'))
    choose_option_prompt = '授业：请选择你的行动'


@ui_meta(characters.keine.TeachTargetReforgeAction)
class TeachTargetReforgeAction:
    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '重铸这张牌')
        else:
            return (False, '请选择一张牌重铸')

    def target(self, pl):
        if not pl:
            return (False, '请选择1名玩家')

        return (True, '传道授业！')


@ui_meta(characters.keine.KeineGuard)
class KeineGuard:
    # Skill
    name = '守护'
    description = (
        '|B觉醒技|r，回合开始阶段，若你已受伤，且的体力值为全场最少或之一，你减少一点体力上限并获得技能|R噬史|r：\n'
        '每轮限一次。一名角色的出牌阶段开始时，你可以弃置一张基本牌，并根据其颜色发动相应效果：\n'
        '|B|R>> |r若为红色，你记录该角色当前的体力值\n'
        '|B|R>> |r若为黑色，你记录该角色当前的手牌数\n'
        '该角色的出牌阶段结束时，将其恢复至本回合记录时的状态。'
    )
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.keine.KeineGuardAwake)
class KeineGuardAwake:
    def effect_string(self, act):
        return '直到满月，人们才回想起被|G【%s】|r的头锤 |BCAVED|r 的恐惧！！！！' % (
            act.target.ui_meta.name
        )

    def sound_effect_before(self, act):
        return random.choice([
            'thb-cv-keine_guard_awake',
        ])


@ui_meta(characters.keine.Keine)
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

    notes = '|RKOF不平衡角色|r'
