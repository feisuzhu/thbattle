# -*- coding: utf-8 -*-


# -- stdlib --
import random

# -- third party --
# -- own --
from thb import characters
from thb.meta.common import ui_meta, N


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
    description = '你攻击范围内的一名其它角色的出牌阶段开始时，你可以对其使用一张<style=Card.Name>弹幕</style>。'


@ui_meta(characters.momiji.Telegnosis)
class Telegnosis:
    # Skill
    name = '千里眼'
    description = '<style=B>锁定技</style>，若你在一名其他角色的攻击范围内，则该角色视为在你攻击范围内。'


@ui_meta(characters.momiji.Disarm)
class Disarm:
    # Skill
    name = '缴械'
    description = '每当你使用<style=Card.Name>弹幕</style>或<style=Card.Name>弹幕战</style>对其他角色造成伤害后，你可以观看其手牌，并将其中任意数量的<style=Card.Name>弹幕</style>或符卡牌暂时移出游戏。该角色被暂时移出的牌会在该角色下一个弃牌阶段后归还回其手牌中。'


@ui_meta(characters.momiji.DisarmHideAction)
class DisarmHideAction:
    def effect_string(self, act):
        return f'{N.char(act.source)}拦下了{N.char(act.target)}，从头到脚检查了一遍。'

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
    choose_option_prompt = '你希望发动<style=Skill.Name>缴械</style>吗？'


@ui_meta(characters.momiji.SentryHandler)
class SentryHandler:
    # choose_option meta
    choose_option_buttons = (('发动', True), ('不发动', False))

    def choose_option_prompt(self, act):
        return f'你希望发动<style=Skill.Name>哨戒</style>吗（对{N.char(act.target)}）？'


@ui_meta(characters.momiji.SentryAction)
class SentryAction:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, f'吃我大弹幕啦！(对{N.char(act.target)}发动哨戒)')
        else:
            return (False, '<style=Skill.Name>哨戒</style>：请选择一张弹幕发动哨戒(对{N.char(act.target)})')


@ui_meta(characters.momiji.SolidShieldHandler)
class SolidShieldHandler:
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你希望发动<style=Skill.Name>坚盾</style>吗？'


@ui_meta(characters.momiji.SolidShieldAction)
class SolidShieldAction:
    def effect_string_before(self, act):
        # return u'“嗷~~~~！”{N.char()}突然冲了出来，吓的{N.char()}手里的%s都掉在地上了。' % (
        return f'“嗷~~~~！”{N.char(act.source)}突然冲了出来，挡在了{N.char(act.action.target)}面前。'

    def sound_effect(self, act):
        return 'thb-cv-momiji_solidshield'


@ui_meta(characters.momiji.SolidShield)
class SolidShield:
    # Skill
    name = '坚盾'
    description = '你距离1以内的角色成为其它角色使用的<style=Card.Name>弹幕</style>或单体符卡的目标后，若此卡牌为其出牌阶段时使用的第一张卡牌，取消之并暂时移出游戏。该角色被暂时移出的牌会在该角色下一个弃牌阶段后归还回其手牌中。'
