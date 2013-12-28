# -*- coding: utf-8 -*-

from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import passive_clickable, passive_is_action_valid
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.nazrin)


class Nazrin:
    # Character
    char_name = u'纳兹琳'
    port_image = gres.nazrin_port
    description = (
        u'|DB探宝的小小大将 纳兹琳 体力：3|r\n\n'
        u'|G轻敏|r：你可以将你的黑色手牌当作【擦弹】使用或打出。\n\n'
        u'|G探宝|r：回合开始阶段，你可以进行判定。判定结束后，若为黑色，你获得此判定牌，并且可以继续发动探宝。'
    )


class TreasureHuntSkill:
    # Skill
    name = u'探宝'
    clickable = passive_clickable
    is_action_valid = passive_is_action_valid


class TreasureHuntHandler:
    # choose_option
    choose_option_buttons = ((u'发动', True), (u'不发动', False))
    choose_option_prompt = u'你要发动【探宝】吗？'


class Agile:
    # Skill
    name = u'轻敏'

    def clickable(game):
        me = game.me

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, cards.BaseUseGraze) and (me.cards or me.showncards):
            return True

        return False

    def is_complete(g, cl):
        skill = cl[0]
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张牌！')
        else:
            c = cl[0]
            if c.resides_in not in (g.me.cards, g.me.showncards):
                return (False, u'请选择手牌！')
            if c.suit not in (cards.Card.SPADE, cards.Card.CLUB):
                return (False, u'请选择一张黑色的牌！')
            return (True, u'这种三脚猫的弹幕，想要打中我是不可能的啦~')


class TreasureHunt:
    name = u'探宝'
    
    def effect_string(act):
        if act.succeeded:
            return u'|G【%s】|r找到了|G%s|r' % (
                act.target.ui_meta.char_name,
                act.card.ui_meta.name,
            )
        else:
            return u'|G【%s】|r什么也没有找到…' % (
                act.target.ui_meta.char_name,
            )
