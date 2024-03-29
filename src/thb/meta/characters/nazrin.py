# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Card
from thb.cards.classes import BaseUseGraze
from thb.meta.common import ui_meta, N


# -- code --
@ui_meta(characters.nazrin.Nazrin)
class Nazrin:
    # Character
    name        = '纳兹琳'
    title       = '探宝的小小大将'
    illustrator = '月见'
    cv          = '小羽'

    port_image        = 'thb-portrait-nazrin'
    figure_image      = 'thb-figure-nazrin'
    miss_sound_effect = 'thb-cv-nazrin_miss'


@ui_meta(characters.nazrin.NazrinKOF)
class NazrinKOF:
    # Character
    name        = '纳兹琳'
    title       = '探宝的小小大将'
    illustrator = '月见'
    cv          = '小羽'

    port_image        = 'thb-portrait-nazrin'
    figure_image      = 'thb-figure-nazrin'
    miss_sound_effect = 'thb-cv-nazrin_miss'

    notes = 'KOF修正角色'


@ui_meta(characters.nazrin.TreasureHunt)
class TreasureHunt:
    # Skill
    name = '探宝'
    description = '准备阶段开始时，你可以进行一次判定，若结果为黑，你获得此牌且你可以重复此流程。'


@ui_meta(characters.nazrin.TreasureHuntHandler)
class TreasureHuntHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动<style=Skill.Name>探宝</style>吗？'


@ui_meta(characters.nazrin.Agile)
class Agile:
    # Skill
    name = '轻敏'
    description = '你可以将一张黑色手牌当<style=Card.Name>擦弹</style>使用或打出。'

    def clickable(self):
        g = self.game
        me = self.me

        try:
            act = g.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, BaseUseGraze) and (me.cards or me.showncards):
            return True

        return False

    def is_complete(self, skill):
        cl = skill.associated_cards
        me = self.me
        if len(cl) != 1:
            return (False, '请选择一张牌！')
        else:
            c = cl[0]
            if c.resides_in not in (me.cards, me.showncards):
                return (False, '请选择手牌！')
            if c.suit not in (Card.SPADE, Card.CLUB):
                return (False, '请选择一张黑色的牌！')
            return (True, '这种三脚猫的弹幕，想要打中我是不可能的啦~')

    def sound_effect(self, act):
        return 'thb-cv-nazrin_agile'


@ui_meta(characters.nazrin.AgileKOF)
class AgileKOF:
    # Skill
    name = '轻敏'
    description = '你可以将一张♠手牌当<style=Card.Name>擦弹</style>使用或打出。'

    clickable = Agile.clickable

    def is_complete(self, skill):
        cl = skill.associated_cards
        me = self.me
        if len(cl) != 1:
            return (False, '请选择一张牌！')
        else:
            c = cl[0]
            if c.resides_in not in (me.cards, me.showncards):
                return (False, '请选择手牌！')
            if c.suit != Card.SPADE:
                return (False, '请选择一张黑桃色手牌牌！')
            return (True, '这种三脚猫的弹幕，想要打中我是不可能的啦~')

    sound_effect = Agile.sound_effect


@ui_meta(characters.nazrin.TreasureHuntAction)
class TreasureHuntAction:
    fatetell_display_name = '探宝'

    def effect_string(self, act):
        tgt = act.target
        if act.succeeded:
            return f'{N.char(tgt)}找到了{N.card(act.card)}'
        else:
            return f'{N.char(tgt)}什么也没有找到…'

    def sound_effect(self, act):
        tgt = act.target
        t = tgt.tags
        if not t['__treasure_hunt_se'] >= t['turn_count']:
            t['__treasure_hunt_se'] = t['turn_count']
            return 'thb-cv-nazrin_treasurehunt'
