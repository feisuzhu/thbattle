# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid

# -- code --
__metaclass__ = gen_metafunc(characters.rumia)


class Darkness:
    # Skill
    name = u'黑暗'
    description = (
        u'出牌阶段限一次，你可以弃置一张牌并指定一名其他角色，令其选择一项：\n'
        u'|B|R>> |r对其攻击范围内另一名你指定的其他角色使用一张|G弹幕|r。\n'
        u'|B|R>> |r受到你造成的1点伤害。'
    )

    custom_ray = True

    def clickable(game):
        try:
            if limit1_skill_used('darkness_tag'):
                return False
            act = game.action_stack[-1]
            if isinstance(act, actions.ActionStage):
                return True
        except IndexError:
            pass
        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        cl = skill.associated_cards
        if not cl or len(cl) != 1:
            return (False, u'请选择一张牌')

        if not len(tl):
            return (False, u'请选择第一名玩家（向第二名玩家出【弹幕】）')
        elif len(tl) == 1:
            return (False, u'请选择第二名玩家（【弹幕】的目标）')
        else:
            return (True, u'你们的关系…是~这样吗？')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r在黑暗中一通乱搅，结果|G【%s】|r和|G【%s】|r打了起来！' % (
            act.source.ui_meta.name,
            act.target_list[0].ui_meta.name,
            act.target_list[1].ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-rumia_darkness'


class DarknessKOF:
    # Skill
    name = u'黑暗'
    description = u'|B登场技|r，你登场的回合，对方使用牌时不能指定你为目标。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DarknessKOFAction:

    def effect_string(act):
        return u'|G【%s】|r一出现天就黑了，低头都看不见胖次！' % act.source.ui_meta.name

    def sound_effect(act):
        return 'thb-cv-rumia_darkness_kof'


class DarknessKOFLimit:
    shootdown_message = u'【黑暗】你不能对其使用卡牌'


class DarknessAction:
    def ray(act):
        src = act.source
        tl = act.target_list
        return [(src, tl[0]), (tl[0], tl[1])]

    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'使用【弹幕】')
        else:
            return (False, u'请使用一张【弹幕】（否则受到一点伤害）')


class Cheating:
    # Skill
    name = u'作弊'
    description = u'|B锁定技|r，结束阶段开始时，你摸一张牌。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class CheatingDrawCards:
    def effect_string(act):
        return u'突然不知道是谁把太阳挡住了。等到大家回过神来，赫然发现牌堆里少了一张牌！'

    def sound_effect(act):
        return 'thb-cv-rumia_cheat'


class Rumia:
    # Character
    name        = u'露米娅'
    title       = u'宵暗的妖怪'
    illustrator = u'和茶'
    cv          = u'小羽'

    port_image        = u'thb-portrait-rumia'
    figure_image      = u'thb-figure-rumia'
    miss_sound_effect = u'thb-cv-rumia_miss'


class RumiaKOF:
    # Character
    name        = u'露米娅'
    title       = u'宵暗的妖怪'
    illustrator = u'和茶'
    cv          = u'小羽'

    port_image        = u'thb-portrait-rumia'
    figure_image      = u'thb-figure-rumia'
    miss_sound_effect = u'thb-cv-rumia_miss'

    notes = u'|RKOF修正角色'
