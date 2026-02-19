# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


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
        '出牌阶段结束时，你可以重铸一张装备牌，然后发动对应的效果：'
        '<style=Desc.Li>武器：视为对一名其他角色使用了<style=Card.Name>弹幕</style>。</style>'
        '<style=Desc.Li>防具：令一名角色回复1点体力。</style>'
        '<style=Desc.Li>饰品：摸一张牌并跳过弃牌阶段。</style>'
        '<style=Desc.Li>UFO：视为使用一张<style=Card.Name>人形操控</style>。</style>'
    )


@ui_meta(characters.alice.LittleLegionAttackCard)
class LittleLegionAttackCard:
    name = '小小军势'

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return f'{N.char(act.source)}操起人偶，向{N.char(act.target)}进攻！'

    def sound_effect(self, act):
        return 'thb-cv-alice_legion_attack'


@ui_meta(characters.alice.LittleLegionDollControlCard)
class LittleLegionDollControlCard:
    name = '小小军势'
    custom_ray = True

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        controllee, victim = act.target_list
        return f'{N.char(act.source)}操起人偶……呃不对，是{N.char(controllee)}，向{N.char(victim)}进攻！'

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
            return f'{N.char(act.target)}回复了{act.amount}点体力。'

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
        g = self.game

        if not pl:
            return (False, '控场：请选择2名玩家，视为使用<style=Card.Name>人形操控</style>')

        from thb.cards.classes import DollControlCard

        rst, prompt = DollControlCard().ui_meta.is_action_valid([], pl)

        if rst:
            return (True, '就让你见识下人偶军团的厉害！')
        else:
            return rst, prompt


@ui_meta(characters.alice.LittleLegionHandler)
class LittleLegionHandler:

    # choose_card
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            c, = cards
            if c.equipment_category == 'weapon':
                text = '（武器）：视为对一名角色使用弹幕。'
            elif c.equipment_category == 'shield':
                text = '（防具）：令一名角色回复一点体力。'
            elif c.equipment_category == 'accessories':
                text = '（饰品）：跳过弃牌阶段。'
            elif c.equipment_category in ('redufo', 'greenufo'):
                text = '（UFO）：视为使用<style=Card.Name>人形操控</style>。'
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


@ui_meta(characters.alice.DollBlastEffect)
class DollBlastEffect:

    def effect_string_before(self, act):
        src, tgt = act.source, act.target
        c = act.card
        if act.do_damage:
            return f'{N.char(tgt)}拿走了{N.char(src)}的人偶（{N.card(c)}），然后，BOOM！{N.char(tgt)}就炸了！'
        else:
            return f'{N.char(tgt)}拿走了{N.char(src)}的人偶，{N.char(src)}非常生气，弃置了{N.char(tgt)}的{N.card(c)}。'


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
    choose_option_prompt = '你要发动<style=Skill.Name>人偶爆弹</style>吗？'

# ----------
