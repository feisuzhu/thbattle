# -*- coding: utf-8 -*-

from gamepack.thb import actions
from gamepack.thb import cards
from gamepack.thb import characters
from gamepack.thb.ui.ui_meta.common import gen_metafunc
from gamepack.thb.ui.ui_meta.common import limit1_skill_used
from gamepack.thb.ui.resource import resource as gres

__metaclass__ = gen_metafunc(characters.eirin)


class FirstAid:
    # Skill
    name = u'急救'

    def clickable(game):
        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, cards.AskForHeal):
            return True

        return False

    def is_complete(g, cl):
        skill = cl[0]
        acards = skill.associated_cards
        C = cards.Card
        if len(acards) != 1 or acards[0].suit not in (C.DIAMOND, C.HEART):
            return (False, u'请选择一张红色牌！')

        return (True, u'k看不到@#@#￥@#￥')

    def sound_effect(act):
        return gres.cv.eirin_firstaid


class Medic:
    # Skill
    name = u'医者'

    def clickable(game):
        me = game.me

        if limit1_skill_used('medic_tag'):
            return False

        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, actions.ActionStage) and (me.cards or me.showncards):
            return True

        return False

    def is_action_valid(g, cl, tl):
        skill = cl[0]
        me = g.me
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, u'请选择一张手牌！')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in cl):
            return (False, u'只能使用手牌发动！')
        elif not tl or len(tl) != 1:
            return (False, u'请选择一名受伤的玩家')
        elif tl[0].maxlife <= tl[0].life:
            return (False, u'这只精神着呢，不用管她')
        return (True, u'少女，身体要紧啊！')

    def effect_string(act):
        # for LaunchCard.ui_meta.effect_string
        return (
            u'|G【%s】|r用一张|G%s|r做药引做了一贴膏药，'
            u'细心地贴在了|G【%s】|r的伤口上。'
        ) % (
            act.source.ui_meta.char_name,
            act.card.associated_cards[0].ui_meta.name,
            act.target.ui_meta.char_name,
        )

    def sound_effect(act):
        return gres.cv.eirin_medic


class Eirin:
    # Character
    char_name = u'八意永琳'
    port_image = gres.eirin_port
    figure_image = gres.eirin_figure
    miss_sound_effect = gres.cv.eirin_miss
    description = (
        u'|DB街中的药贩 八意永琳 体力：3|r\n\n'
        u'|G医者|r：出牌阶段，你可以主动弃掉一张手牌，令任一目标角色回复1点体力。每回合限一次。\n\n'
        u'|G急救|r：当任意人进入濒死状态时，你可以将你的红色手牌或装备牌当做【麻薯】使用。\n\n'
        u'|RKOF不平衡角色\n\n'
        u'|DB（画师：渚FUN，CV：VV）|r'
    )
