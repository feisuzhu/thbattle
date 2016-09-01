# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, cards, characters
from thb.ui.ui_meta.common import gen_metafunc, limit1_skill_used

# -- code --
__metaclass__ = gen_metafunc(characters.eirin)


class FirstAid:
    # Skill
    name = u'急救'
    description = u'你可以将一张红色牌当|G麻薯|r对濒死角色使用。'

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
        return 'thb-cv-eirin_firstaid'


class Medic:
    # Skill
    name = u'医者'
    description = u'出牌阶段限一次，你可以弃置一张手牌令一名已受伤的角色回复1点残机。'

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
            act.source.ui_meta.name,
            act.card.associated_cards[0].ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(act):
        return 'thb-cv-eirin_medic'


class Eirin:
    # Character
    name        = u'八意永琳'
    title       = u'街中的药贩'
    illustrator = u'渚FUN'
    cv          = u'VV'

    port_image        = u'thb-portrait-eirin'
    figure_image      = u'thb-figure-eirin'
    miss_sound_effect = u'thb-cv-eirin_miss'

    notes = u'|RKOF模式不可用|r'
