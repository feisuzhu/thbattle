# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.ui.ui_meta.common import G, card_desc, gen_metafunc, passive_clickable
from thb.ui.ui_meta.common import passive_is_action_valid


# -- code --
__metaclass__ = gen_metafunc(characters.alice)


class Alice:
    # Character
    name        = u'爱丽丝'
    title       = u'七色的人偶使'
    illustrator = u'霏茶'
    cv          = u'小舞'

    port_image        = 'thb-portrait-alice'
    figure_image      = 'thb-figure-alice'
    miss_sound_effect = 'thb-cv-alice_miss'


class LittleLegion:
    # Skill
    name = u'小小军势'
    description = (
        u'出牌阶段结束时，你可以重铸一张装备牌，然后发动对应的效果：\n'
        u'|B|R>> |r武器：视为对一名其他角色使用了|G弹幕|r。\n'
        u'|B|R>> |r防具：令一名角色回复1点体力。\n'
        u'|B|R>> |r饰品：摸一张牌并跳过弃牌阶段。\n'
        u'|B|R>> |rUFO：视为使用一张|G人型操控|r。'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class LittleLegionAttackCard:
    name = u'小小军势'

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return u'|G【%s】|r操起人偶，向|G【%s】|r进攻！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-alice_legion_attack'


class LittleLegionDollControlCard:
    name = u'小小军势'
    custom_ray = True

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        controllee, victim = act.target_list
        return u'|G【%s】|r操起人偶……呃不对，是|G【%s】|r，向|G【%s】|r进攻！' % (
            act.source.ui_meta.name,
            controllee.ui_meta.name,
            victim.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-alice_legion_control'


class LittleLegionAttackAction:

    def target(pl):
        if not pl:
            return (False, u'进攻：请选择1名玩家，视为使用弹幕')

        return (True, u'就让你见识下人偶军团的厉害！')


class LittleLegionCoverEffect:
    def effect_string(act):
        if act.succeeded:
            return u'|G【%s】|r回复了%d点体力。' % (
                act.target.ui_meta.name, act.amount
            )

    def sound_effect(act):
        return 'thb-cv-alice_legion_cover'


class LittleLegionCoverAction:

    def target(pl):
        if not pl:
            return (False, u'掩护：请选择1名玩家，回复1点体力')

        return (True, u'支援到了，重复，支援到了！')


class LittleLegionHoldAction:

    def sound_effect(act):
        return 'thb-cv-alice_legion_hold'


class LittleLegionControlAction:

    def target(pl):
        if not pl:
            return (False, u'控场：请选择2名玩家，视为使用【人型操控】')

        from thb.cards import DollControlCard

        rst, prompt = DollControlCard.ui_meta.is_action_valid(G(), [], pl)

        if rst:
            return (True, u'就让你见识下人偶军团的厉害！')
        else:
            return rst, prompt


class LittleLegionHandler:

    # choose_card
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            c, = cards
            if c.equipment_category == 'weapon':
                text = u'（武器）：视为对一名角色使用弹幕。'
            elif c.equipment_category == 'shield':
                text = u'（防具）：令一名角色回复一点体力。'
            elif c.equipment_category == 'accessories':
                text = u'（饰品）：跳过弃牌阶段。'
            elif c.equipment_category in ('redufo', 'greenufo'):
                text = u'（UFO）：视为使用人型操控。'
            else:
                text = u'（BUG）：什么鬼……'

            return (True, u'小小军势' + text)
        else:
            return (False, u'小小军势：重铸一张装备牌，发动相应效果（否则不发动）')


class DollBlast:
    # Skill
    name = u'人偶爆弹'
    description = u'每当你装备区的牌被其他角色获得或弃置时，你可以弃置其一张牌。若此法弃置的牌为该角色获得的牌，你对其造成1点伤害。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class DollBlastEffect:

    def effect_string_before(act):
        if act.do_damage:
            return u'|G【%s】|r拿走了|G【%s】|r的人偶（%s），然后，BOOM！|G【%s】|r就炸了！' % (
                act.target.ui_meta.name,
                act.source.ui_meta.name,
                card_desc(act.card),
                act.target.ui_meta.name,
            )
        else:
            return u'|G【%s】|r拿走了|G【%s】|r的人偶，|G【%s】|r非常生气，弃置|G【%s】|r的%s。' % (
                act.target.ui_meta.name,
                act.source.ui_meta.name,
                act.source.ui_meta.name,
                act.target.ui_meta.name,
                card_desc(act.card),
            )


class DollBlastAction:

    def sound_effect(act):
        return random.choice([
            'thb-cv-alice_dollblast_blast',
            'thb-cv-alice_dollblast_noblast',
        ])


class DollBlastHandlerCommon:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【人偶爆弹】吗？'

# ----------
