# -*- coding: utf-8 -*-

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import G, card_desc, ui_meta, passive_clickable
from thb.meta.common import passive_is_action_valid


# -- code --


@ui_meta(characters.alice.Alice)
class Alice:
    # Character
    name        = '爱丽丝'
    title       = '七色的人偶使'
    illustrator = '霏茶'
    cv          = '小舞'

    port_image        = 'thb-portrait-alice'
    figure_image      = 'thb-figure-alice'
    miss_sound_effect = 'thb-cv-alice_miss'


@ui_meta(characters.alice.LittleLegion)
class LittleLegion:
    # Skill
    name = '小小军势'
    description = (
        '出牌阶段结束时，你可以重铸一张装备牌，然后发动对应的效果：\n'
        '|B|R>> |r武器：视为对一名其他角色使用了|G弹幕|r\n'
        '|B|R>> |r防具：令一名角色回复1点体力\n'
        '|B|R>> |r饰品：摸一张牌并跳过弃牌阶段\n'
        '|B|R>> |rUFO ：视为使用一张|G人型操控|r'
    )

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.alice.LittleLegionAttackCard)
class LittleLegionAttackCard:
    name = '小小军势'

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return '|G【%s】|r操起人偶，向|G【%s】|r进攻！' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-alice_legion_attack'


@ui_meta(characters.alice.LittleLegionDollControlCard)
class LittleLegionDollControlCard:
    name = '小小军势'
    custom_ray = True

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        controllee, victim = act.target_list
        return '|G【%s】|r操起人偶……呃不对，是|G【%s】|r，向|G【%s】|r进攻！' % (
            act.source.ui_meta.name,
            controllee.ui_meta.name,
            victim.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-alice_legion_control'


@ui_meta(characters.alice.LittleLegionAttackAction)
class LittleLegionAttackAction:

    def target(self, pl):
        if not pl:
            return (False, '进攻：请选择1名玩家，视为使用弹幕')

        return (True, '就让你见识下人偶军团的厉害！')


@ui_meta(characters.alice.LittleLegionCoverEffect)
class LittleLegionCoverEffect:
    def effect_string(self, act):
        if act.succeeded:
            return '|G【%s】|r回复了%d点体力。' % (
                act.target.ui_meta.name, act.amount
            )

    def sound_effect(self, act):
        return 'thb-cv-alice_legion_cover'


@ui_meta(characters.alice.LittleLegionCoverAction)
class LittleLegionCoverAction:

    def target(self, pl):
        if not pl:
            return (False, '掩护：请选择1名玩家，回复1点体力')

        return (True, '支援到了，重复，支援到了！')


@ui_meta(characters.alice.LittleLegionHoldAction)
class LittleLegionHoldAction:

    def sound_effect(self, act):
        return 'thb-cv-alice_legion_hold'


@ui_meta(characters.alice.LittleLegionControlAction)
class LittleLegionControlAction:

    def target(self, pl):
        if not pl:
            return (False, '控场：请选择2名玩家，视为使用【人型操控】')

        from thb.cards.classes import DollControlCard

        rst, prompt = DollControlCard.ui_meta.is_action_valid(G(), [], pl)

        if rst:
            return (True, '就让你见识下人偶军团的厉害！')
        else:
            return rst, prompt


@ui_meta(characters.alice.LittleLegionHandler)
class LittleLegionHandler:

    # choose_card
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            c, = cards
            if c.equipment_category == 'weapon':
                text = '（武器）：视为对一名角色使用弹幕'
            elif c.equipment_category == 'shield':
                text = '（防具）：令一名角色回复一点体力'
            elif c.equipment_category == 'accessories':
                text = '（饰品）：跳过弃牌阶段'
            elif c.equipment_category in ('redufo', 'greenufo'):
                text = '（UFO）：视为使用人型操控'
            else:
                text = '（BUG）：什么鬼……'

            return (True, '小小军势' + text)
        else:
            return (False, '小小军势：重铸一张装备牌，发动相应效果（否则不发动）')


@ui_meta(characters.alice.DollBlast)
class DollBlast:
    # Skill
    name = '人偶爆弹'
    description = '每当你装备区的牌被其他角色获得或弃置时，你可以弃置其一张牌。若此法弃置的牌为该角色获得的牌，你对其造成1点伤害。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.alice.DollBlastEffect)
class DollBlastEffect:

    def effect_string_before(self, act):
        if act.do_damage:
            return '|G【%s】|r拿走了|G【%s】|r的人偶（%s），然后，BOOM！|G【%s】|r就炸了！' % (
                act.target.ui_meta.name,
                act.source.ui_meta.name,
                card_desc(act.card),
                act.target.ui_meta.name,
            )
        else:
            return '|G【%s】|r拿走了|G【%s】|r的人偶，|G【%s】|r非常生气，弃置|G【%s】|r的%s。' % (
                act.target.ui_meta.name,
                act.source.ui_meta.name,
                act.source.ui_meta.name,
                act.target.ui_meta.name,
                card_desc(act.card),
            )


@ui_meta(characters.alice.DollBlastAction)
class DollBlastAction:

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-alice_dollblast_blast',
            'thb-cv-alice_dollblast_noblast',
        ])


@ui_meta(characters.alice.DollBlastHandlerCommon)
class DollBlastHandlerCommon:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【人偶爆弹】吗？'

# ----------
