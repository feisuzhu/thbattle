# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb import actions, characters
from thb.cards.classes import AskForHeal
from thb.cards.base import Card
from thb.meta.common import ui_meta, limit1_skill_used

# -- code --


@ui_meta(characters.eirin.FirstAid)
class FirstAid:
    # Skill
    name = '急救'
    description = '你可以将一张红色牌当|G麻薯|r对濒死角色使用。'

    def clickable(self, game):
        try:
            act = game.action_stack[-1]
        except IndexError:
            return False

        if isinstance(act, AskForHeal):
            return True

        return False

    def is_complete(self, g, skill):
        acards = skill.associated_cards
        if len(acards) != 1 or acards[0].suit not in (Card.DIAMOND, Card.HEART):
            return (False, '请选择一张红色牌！')

        return (True, 'k看不到@#@#￥@#￥')

    def sound_effect(self, act):
        return 'thb-cv-eirin_firstaid'


@ui_meta(characters.eirin.Medic)
class Medic:
    # Skill
    name = '医者'
    description = '出牌阶段限一次，你可以弃置一张手牌令一名已受伤的角色回复1点体力。'

    def clickable(self, game):
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

    def is_action_valid(self, g, cl, tl):
        skill = cl[0]
        me = g.me
        cl = skill.associated_cards
        if len(cl) != 1:
            return (False, '请选择一张手牌！')
        elif any(c.resides_in not in (me.cards, me.showncards) for c in cl):
            return (False, '只能使用手牌发动！')
        elif not tl or len(tl) != 1:
            return (False, '请选择一名受伤的玩家')
        elif tl[0].maxlife <= tl[0].life:
            return (False, '这只精神着呢，不用管她')
        return (True, '少女，身体要紧啊！')

    def effect_string(self, act):
        # for LaunchCard.ui_meta.effect_string
        return (
            '|G【%s】|r用一张|G%s|r做药引做了一贴膏药，'
            '细心地贴在了|G【%s】|r的伤口上。'
        ) % (
            act.source.ui_meta.name,
            act.card.associated_cards[0].ui_meta.name,
            act.target.ui_meta.name,
        )

    def sound_effect(self, act):
        return 'thb-cv-eirin_medic'


@ui_meta(characters.eirin.Eirin)
class Eirin:
    # Character
    name        = '八意永琳'
    title       = '街中的药贩'
    illustrator = '渚FUN'
    cv          = 'VV'

    port_image        = 'thb-portrait-eirin'
    figure_image      = 'thb-figure-eirin'
    miss_sound_effect = 'thb-cv-eirin_miss'

    notes = '|RKOF模式不可用|r'
