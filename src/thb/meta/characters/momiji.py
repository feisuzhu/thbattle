# -*- coding: utf-8 -*-


# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, passive_clickable, passive_is_action_valid


# -- code --


@ui_meta(characters.momiji.Momiji)
class Momiji:
    # Character
    name        = '犬走椛'
    title       = '山中的千里眼'
    illustrator = '和茶'
    cv          = '简翎'

    port_image        = 'thb-portrait-momiji'
    figure_image      = 'thb-figure-momiji'
    miss_sound_effect = 'thb-cv-momiji_miss'


@ui_meta(characters.momiji.Sentry)
class Sentry:
    # Skill
    name = '哨戒'
    description = '你攻击范围内的一名其它角色的出牌阶段开始时，你可以对其使用一张|G弹幕|r。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.momiji.Telegnosis)
class Telegnosis:
    # Skill
    name = '千里眼'
    description = '|B锁定技|r，若你在一名其他角色的攻击范围内，则该角色视为在你攻击范围内。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.momiji.Disarm)
class Disarm:
    # Skill
    name = '缴械'
    description = '每当你使用|G弹幕|r或|G弹幕战|r对其他角色造成伤害后，你可以观看其手牌，并将其中任意数量的|G弹幕|r或符卡牌暂时移出游戏。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.momiji.DisarmHideAction)
class DisarmHideAction:
    def effect_string(self, act):
        return '|G【%s】|r拦下了|G【%s】|r，从头到脚检查了一遍。' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-momiji_disarm'


@ui_meta(characters.momiji.SentryAttack)
class SentryAttack:
    # Skill
    name = '哨戒'

    def sound_effect(self, act):
        return random.choice([
            'thb-cv-momiji_sentry1',
            'thb-cv-momiji_sentry2',
        ])


@ui_meta(characters.momiji.DisarmHandler)
class DisarmHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你希望发动【缴械】吗？'


@ui_meta(characters.momiji.SentryHandler)
class SentryHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))

    def choose_option_prompt(self, act):
        return '你希望发动【哨戒】吗（对%s）？' % act.target.ui_meta.name


@ui_meta(characters.momiji.SentryAction)
class SentryAction:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '吃我大弹幕啦！(对%s发动哨戒)' % act.target.ui_meta.name)
        else:
            return (False, '哨戒：请选择一张弹幕发动哨戒(对%s)' % act.target.ui_meta.name)


@ui_meta(characters.momiji.SolidShieldHandler)
class SolidShieldHandler:
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你希望发动【坚盾】吗？'


@ui_meta(characters.momiji.SolidShieldAction)
class SolidShieldAction:
    def effect_string_before(self, act):
        # return u'“嗷~~~~！”|G【%s】|r突然冲了出来，吓的|G【%s】|r手里的%s都掉在地上了。' % (
        return '“嗷~~~~！”|G【%s】|r突然冲了出来，挡在了|G【%s】|r面前。' % (
            act.source.ui_meta.name,
            act.action.target.ui_meta.name,
            # card_desc(act.action.card),
        )

    def sound_effect(self, act):
        return 'thb-cv-momiji_solidshield'


@ui_meta(characters.momiji.SolidShield)
class SolidShield:
    # Skill
    name = '坚盾'
    description = '你距离1以内的角色成为其它角色使用的|G弹幕|r或单体符卡的目标后，若此卡牌为其出牌阶段时使用的第一张卡牌，取消之并暂时移出游戏。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid
