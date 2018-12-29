# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import characters
from thb.cards.base import Card
from thb.cards.classes import BaseUseGraze
from thb.meta.common import passive_clickable, passive_is_action_valid, ui_meta


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

    notes = '|RKOF修正角色|r'


@ui_meta(characters.nazrin.TreasureHunt)
class TreasureHunt:
    # Skill
    name = '探宝'
    description = '准备阶段开始时，你可以进行一次判定，若结果为黑，你获得此牌且你可以重复此流程。'

    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


@ui_meta(characters.nazrin.TreasureHuntHandler)
class TreasureHuntHandler:
    # choose_option
    choose_option_buttons = (('发动', True), ('不发动', False))
    choose_option_prompt = '你要发动【探宝】吗？'


@ui_meta(characters.nazrin.Agile)
class Agile:
    # Skill
    name = '轻敏'
    description = '你可以将一张黑色手牌当|G擦弹|r使用或打出。'

    def clickable(self, game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, BaseUseGraze) and (me.cards or me.showncards):
            return True

        return False

    def is_complete(self, g, skill):
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, '请选择一张牌！')
        else:
            c = cl[0]
            if c.resides_in not in (g.me.cards, g.me.showncards):
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
    description = '你可以将一张|B黑桃|r手牌当|G擦弹|r使用或打出。'

    clickable = Agile.clickable

    def is_complete(self, g, skill):
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, '请选择一张牌！')
        else:
            c = cl[0]
            if c.resides_in not in (g.me.cards, g.me.showncards):
                return (False, '请选择手牌！')
            if c.suit != Card.SPADE:
                return (False, '请选择一张黑桃色手牌牌！')
            return (True, '这种三脚猫的弹幕，想要打中我是不可能的啦~')

    sound_effect = Agile.sound_effect


@ui_meta(characters.nazrin.TreasureHuntAction)
class TreasureHuntAction:
    fatetell_display_name = '探宝'

    def effect_string(self, act):
        if act.succeeded:
            return '|G【%s】|r找到了|G%s|r' % (
                act.target.ui_meta.name,
                act.card.ui_meta.name,
            )
        else:
            return '|G【%s】|r什么也没有找到…' % (
                act.target.ui_meta.name,
            )

    def sound_effect(self, act):
        tgt = act.target
        t = tgt.tags
        if not t['__treasure_hunt_se'] >= t['turn_count']:
            t['__treasure_hunt_se'] = t['turn_count']
            return 'thb-cv-nazrin_treasurehunt'
