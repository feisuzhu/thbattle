# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.meta.common import ui_meta, N


# -- code --


@ui_meta(characters.kanako.Kanako)
class Kanako:
    # Character
    name        = '八坂神奈子'
    title       = '山丘与湖泊的化身'
    illustrator = '和茶'
    cv          = '北斗夜/VV'

    port_image        = 'thb-portrait-kanako'
    figure_image      = 'thb-figure-kanako'
    miss_sound_effect = 'thb-cv-kanako_miss'

    notes = 'KOF模式不可用'


@ui_meta(characters.kanako.KanakoKOF)
class KanakoKOF:
    # Character
    name        = '八坂神奈子'
    title       = '山丘与湖泊的化身'
    illustrator = '和茶'
    cv          = '北斗夜/VV'

    port_image        = 'thb-portrait-kanako'
    figure_image      = 'thb-figure-kanako'
    miss_sound_effect = 'thb-cv-kanako_miss'

    notes = 'KOF修正角色'


@ui_meta(characters.kanako.KanakoFaith)
class KanakoFaith:
    # Skill
    name = '信仰'
    description = (
        '<style=B>限定技</style>，出牌阶段，你可以令你攻击范围内的所有其他角色依次选择一项：'
        '<style=Desc.Li>令你摸一张牌。</style>'
        '<style=Desc.Li>弃置你一张牌，然后你视为对其使用了一张<style=Card.Name>弹幕</style>或<style=Card.Name>弹幕战</style>（按此法使用的弹幕不消耗干劲）。</style>'
    )

    def clickable(self):
        g = self.game
        me = self.me
        if me.tags['kanako_faith']:
            return False

        try:
            act = g.action_stack[-1]
            if isinstance(act, actions.ActionStage) and act.target is me:
                return True

        except IndexError:
            pass

        return False

    def is_action_valid(self, sk, tl):
        cl = sk.associated_cards
        if cl:
            return (False, '请不要选择牌')

        if not tl:
            return (False, '没有符合条件的角色')
        else:
            return (True, '发动<style=Skill.Name>信仰</style>')

    def effect_string(self, act):
        return f'{N.char(act.source)}打开神社大门，开始收集<style=Skill.Name>信仰</style>！{N.char(act.target_list)}表示很感兴趣。'

    def sound_effect(self, act):
        return 'thb-cv-kanako_faith'

    def is_available(self, ch):
        return not bool(ch.tags['kanako_faith'])


@ui_meta(characters.kanako.KanakoFaithCheers)
class KanakoFaithCheers:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}献上了信仰！'


@ui_meta(characters.kanako.KanakoFaithCounteract)
class KanakoFaithCounteract:
    def effect_string_before(self, act):
        return f'{N.char(act.source)}决定要拆台！'


@ui_meta(characters.kanako.KanakoFaithCounteractPart1)
class KanakoFaithCounteractPart1:
    def effect_string(self, act):
        return f'{N.char(act.source)}弃置了{N.char(act.target)}的{N.card(act.card)}。'


@ui_meta(characters.kanako.KanakoFaithCounteractPart2)
class KanakoFaithCounteractPart2:
    # choose_option meta
    choose_option_buttons = (('弹幕战', 'duel'), ('弹幕', 'attack'))
    choose_option_prompt = '<style=Skill.Name>信仰</style>：请选择希望的效果'


@ui_meta(characters.kanako.KanakoFaithEffect)
class KanakoFaithEffect:
    # choose_option meta
    choose_option_buttons = (('弃置对方的牌', 'drop'), ('对方摸牌', 'draw'))
    choose_option_prompt = '<style=Skill.Name>信仰</style>：请选择希望的效果'


@ui_meta(characters.kanako.Virtue)
class Virtue:
    # Skill
    name = '神德'
    description = '摸牌阶段，你可以放弃摸牌，改为令一名其他角色摸两张牌，然后其须展示并交给你一张牌，若交给你的牌为红桃牌，你摸一张牌。'


@ui_meta(characters.kanako.VirtueHandler)
class VirtueHandler:
    def target(self, pl):
        if not pl:
            return (False, '<style=Skill.Name>神德</style>：请选择1名玩家')

        return (True, '<style=Skill.Name>神德</style>：放弃摸牌，选定的目标摸2张牌')


@ui_meta(characters.kanako.VirtueAction)
class VirtueAction:
    def choose_card_text(self, act, cards):
        prompt = '<style=Skill.Name>神德</style>：交给对方一张牌'
        return act.cond(cards), prompt

    def effect_string_before(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}发动了<style=Skill.Name>神德</style>。'

    def effect_string(self, act):
        return f'{N.char(act.target)}归还了{N.card(act.card_shadow)}。'

    def sound_effect(self, act):
        return 'thb-cv-kanako_virtue'


@ui_meta(characters.kanako.KanakoFaithKOF)
class KanakoFaithKOF:
    # Skill
    name = '信仰'
    description = (
        '<style=B>锁定技</style>，结束阶段开始时，若你满足以下条件之一，将你的手牌补至X张（X为你的当前体力值）：'
        '<style=Desc.Li>你的体力值大于对方。\n'
        '<style=Desc.Li>你曾于出牌阶段对对方造成过伤害。\n'

    )


@ui_meta(characters.kanako.KanakoFaithKOFAction)
class KanakoFaithKOFAction:
    def effect_string_before(self, act):
        return f'{N.char(act.target)}又收到的{act.amount}张香火钱，比博丽神社不知道高到哪里去了！'

    def sound_effect(self, act):
        return 'thb-cv-kanako_faith'
